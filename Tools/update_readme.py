##########################################################################
# If not stated otherwise in this file or this component's LICENSE
# file the following copyright and licenses apply:
#
# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##########################################################################

import sys
import io
import requests
import xml.etree.ElementTree as ET
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class Logger:
    LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}
    def __init__(self, level="info"):
        self.level = self.LEVELS.get(level, 20)
    def debug(self, msg):
        if self.level <= self.LEVELS["debug"]:
            print(f"[DEBUG] {msg}")
    def info(self, msg):
        if self.level <= self.LEVELS["info"]:
            print(f"[INFO] {msg}")
    def warn(self, msg):
        if self.level <= self.LEVELS["warn"]:
            print(f"[WARN] {msg}")
    def error(self, msg):
        if self.level <= self.LEVELS["error"]:
            print(f"[ERROR] {msg}")


# Default configurations.
MLPREFIX = "lib32-"
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN", "")
# Tag prefixes to try while resolving GitHub tags. First entry "" means exact tag.
TAG_PREFIXES = ["", "v", "R", "wpewebkit-"]
# Change to "debug" or "info" for more verbose logging
log = Logger(os.environ.get("LOG_LEVEL", "warn"))

# Number of threads for parallel hyperlinking
def get_default_num_threads():
    try:
        cpu = os.cpu_count() or 4
        log.debug(f"os.cpu_count() returned: {cpu}")
    except Exception:
        log.debug("os.cpu_count() returned None or caused an exception, defaulting to 4 threads.")
        cpu = 4
    # API-bound work does not benefit from very high concurrency by default.
    return min(cpu, 16)

_default_threads = get_default_num_threads()
_raw_threads = os.environ.get("NUM_THREADS", "")
try:
    NUM_THREADS = max(1, int(_raw_threads)) if _raw_threads else _default_threads
except ValueError:
    log.warn(f"Invalid NUM_THREADS value '{_raw_threads}'; defaulting to {_default_threads}")
    NUM_THREADS = _default_threads
# Delay between thread submissions (seconds). Set >0 to throttle GitHub API calls.
try:
    SUBMIT_DELAY_SEC = max(0.0, float(os.environ.get("SUBMIT_DELAY_SEC", "0")))
except ValueError:
    log.warn("Invalid SUBMIT_DELAY_SEC value; defaulting to 0")
    SUBMIT_DELAY_SEC = 0.0
TAG_LOOKUP_CACHE = {}
TAG_LOOKUP_CACHE_LOCK = Lock()

# Check if a GitHub tag exists using GitHub API and return the matched tag (or None)
def find_github_tag(org, repo, tag):
    cache_key = (org, repo, tag)
    with TAG_LOOKUP_CACHE_LOCK:
        if cache_key in TAG_LOOKUP_CACHE:
            return TAG_LOOKUP_CACHE[cache_key]

    candidates = []
    for prefix in TAG_PREFIXES:
        candidate = f"{prefix}{tag}" if prefix else tag
        # Skip if tag already starts with this prefix
        if candidate not in candidates and not (prefix and tag.startswith(prefix)):
            candidates.append(candidate)

    headers = {}
    if GITHUB_API_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_API_TOKEN}'

    # Check each candidate tag directly via git refs.
    # This avoids paginating /tags and also avoids separate /releases probes.
    now = time.time()
    with TAG_LOOKUP_CACHE_LOCK:
        rate_limited_until = getattr(find_github_tag, "_rate_limited_until", 0.0)
    if now < rate_limited_until:
        raise RuntimeError("GitHub API tag lookups are temporarily rate-limited")

    saw_transient_issue = False
    for candidate in candidates:
        candidate_ref = requests.utils.quote(candidate, safe='')
        url = f"https://api.github.com/repos/{org}/{repo}/git/ref/tags/{candidate_ref}"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                with TAG_LOOKUP_CACHE_LOCK:
                    TAG_LOOKUP_CACHE[cache_key] = candidate
                return candidate
            if resp.status_code == 404:
                continue
            if resp.status_code == 401:
                log.error("GitHub API authentication failed. Check GITHUB_API_TOKEN.")
                with TAG_LOOKUP_CACHE_LOCK:
                    TAG_LOOKUP_CACHE[cache_key] = None
                return None
            if resp.status_code in (403, 429):
                retry_after = resp.headers.get("Retry-After", "")
                try:
                    delay = float(retry_after) if retry_after else 60.0
                except ValueError:
                    delay = 60.0
                with TAG_LOOKUP_CACHE_LOCK:
                    find_github_tag._rate_limited_until = time.time() + delay
                log.error("API rate limit exceeded or access forbidden. Try using GITHUB_API_TOKEN or try again later.")
                saw_transient_issue = True
                break
            log.debug(f"Unexpected status checking git ref for tag {candidate}: {resp.status_code}")
            saw_transient_issue = True
        except requests.exceptions.RequestException as e:
            log.debug(f"Request error checking git ref for tag {candidate}: {e}")
            saw_transient_issue = True
            continue
    # Cache negative results for definitive misses (all 404s).
    # Auth failures (401) are cached above; transient/network/rate-limit paths are not.
    if saw_transient_issue:
        raise RuntimeError("Unable to validate GitHub tags due to transient GitHub API/network errors")
    with TAG_LOOKUP_CACHE_LOCK:
        TAG_LOOKUP_CACHE[cache_key] = None
    return None

# Hyperlink package versions in PackagesAndVersions.md
# throw error if required files are not accessible or missing
def parse_component_urls_conf(conf_path):
    url_map = {}
    try:
        with io.open(conf_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    url_map[k.strip()] = v.strip()
    except Exception as e:
        log.error(f"Error reading {conf_path}: {e}")
        sys.exit(1)
    return url_map

def hyperlink_constructor(pkg, base_url, version):
    # Simple tarball or ipk
    if base_url.endswith(('.tar.gz', '.tar.xz', '.tar.bz2', '.ipk')):
        return f'[{version} (artifact)]({base_url})'
    # For GitHub repo
    if 'github.com' in base_url:
        repo_match = re.match(r'https://github.com/([^/]+)/([^/]+)', base_url)
        if repo_match:
            org, repo = repo_match.groups()
            # Trim -r... suffix from version for tag
            trimmed_version = re.sub(r'-r\d+$', '', version)
            log.debug(f"Checking GitHub tag {trimmed_version} for {pkg} in repo {repo}")
            matched_tag = find_github_tag(org, repo, trimmed_version)
            if matched_tag:
                log.info(f"Valid tag {matched_tag} found for {pkg} in repo {repo}")
                return f'[{matched_tag}](https://github.com/{org}/{repo}/tree/{matched_tag})'
            else:
                log.warn(f"No matching tag {trimmed_version} found for {pkg} in repo {repo}, leaving as plain text.")
                return trimmed_version
    # TODO: Implement for code.rdkcentral.com hosted repos
    if 'code.rdkcentral.com' in base_url:
        log.warn(f"Best-effort hyperlink for code.rdkcentral.com (not validated) for {pkg}.")
        return f'[{version}]({base_url}/+/{version})'
    # For meta layer hosted files, no link
    if 'MetaLayerHostedFiles' in base_url:
        if '(layer hosted)' in version:
            return version
        else:
            return f'{version} (layer hosted)'
    # Default: just link to base_url
    return f'[{version}]({base_url})'

def update_package_versions_md(md_path, url_map):
    try:
        with io.open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        log.error(f"Error reading {md_path}: {e}")
        sys.exit(1)


    # Collect jobs for each row without deduplication
    jobs = []
    for idx, line in enumerate(lines):
        # Skip lines that already contain a Markdown hyperlink
        if re.search(r'\[[^\]]+\]\([^\)]+\)', line):
            log.info(f"Skipping line {idx + 1} as it already contains a hyperlink ({line.strip()}).")
            continue
        m = re.match(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', line)
        if m:
            pkg, ver = m.group(1).strip(), m.group(2).strip()
            comp_name = pkg[len(MLPREFIX):] if pkg.startswith(MLPREFIX) else pkg
            base_url = url_map.get(comp_name)
            if base_url and ver:
                jobs.append((idx, pkg, ver, base_url))

    log.info(f"Processing {md_path}: jobs={len(jobs)}, max_workers={NUM_THREADS}")

    # Run hyperlink_constructor in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        future_to_job = {}
        for idx, pkg, ver, base_url in jobs:
            future = executor.submit(hyperlink_constructor, pkg, base_url, ver)
            future_to_job[future] = (idx, pkg, ver, base_url)
            if SUBMIT_DELAY_SEC > 0:
                time.sleep(SUBMIT_DELAY_SEC)
        for future in as_completed(future_to_job):
            idx, pkg, ver, base_url = future_to_job[future]
            try:
                link = future.result()
                results[idx] = f'| {pkg} | {link} |\n'
            except Exception as e:
                log.error(f"Error hyperlinking {pkg}: {e}")
                results[idx] = lines[idx]  # fallback to original line

    # Build new lines
    new_lines = []
    for idx, line in enumerate(lines):
        if idx in results:
            new_lines.append(results[idx])
        else:
            new_lines.append(line)
    with io.open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

# Remove XML comments to avoid parsing commented or disabled sections
COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

def fetch_manifest_xml(manifest_url):
    log.debug(f"Fetching manifest XML: {manifest_url}")
    try:
        resp = requests.get(manifest_url, timeout=10)
        if resp.status_code != 200:
            log.error(f"Failed to fetch manifest XML from {manifest_url} (status={resp.status_code})")
            sys.exit(1)
        return resp.text
    except requests.exceptions.Timeout:
        log.error(f"Timeout fetching manifest XML from {manifest_url}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching manifest XML from {manifest_url}: {e}")
        sys.exit(1)

def parse_manifest(xml_text, manifest_url, release_tag, processed_manifests=None, remote_table=None, project_table=None):
    # Remove XML comments
    xml_text = COMMENT_RE.sub('', xml_text)
    try:
        tree = ET.ElementTree(ET.fromstring(xml_text))
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse manifest XML from {manifest_url}: {e}")
    root = tree.getroot()
    if processed_manifests is None:
        processed_manifests = set()
    if remote_table is None:
        remote_table = {}
    if project_table is None:
        project_table = []
    # Avoid cycles
    if manifest_url in processed_manifests:
        return remote_table, project_table
    processed_manifests.add(manifest_url)

    # Build remote table
    for remote in root.findall('remote'):
        name = remote.get('name')
        fetch = remote.get('fetch')
        if name and fetch:
            remote_table[name] = fetch

    # Read manifest defaults so projects can inherit remote/revision.
    default_elem = root.find('default')
    default_remote = default_elem.get('remote') if default_elem is not None else None
    default_revision = default_elem.get('revision') if default_elem is not None else None

    # Build project table
    for project in root.findall('project'):
        name = project.get('name')
        remote = project.get('remote') or default_remote
        revision = project.get('revision') or default_revision
        if name and revision:
            project_table.append({'name': name, 'remote': remote, 'revision': revision})

    # Recursively process includes
    for include in root.findall('include'):
        inc_name = include.get('name')
        inc_remote = include.get('remote')
        inc_tag = include.get('revision') if include.get('revision') else release_tag
        if not inc_name:
            continue
        # Determine fetch URL
        if inc_remote and inc_remote in remote_table:
            fetch_url = remote_table[inc_remote]
        else:
            # Use current manifest's repo URL (repository root, without tag/file)
            fetch_url = manifest_url.rsplit('/', 2)[0]
        # Convert github.com to raw.githubusercontent.com for fetching manifests
        if fetch_url.startswith("https://github.com"):
            fetch_url = fetch_url.replace("https://github.com", "https://raw.githubusercontent.com")
        fetch_url = fetch_url.rstrip('/')
        # Build manifest URL
        url = f"{fetch_url}/{inc_tag}/{inc_name}"
        inc_xml = fetch_manifest_xml(url)
        parse_manifest(inc_xml, url, inc_tag, processed_manifests, remote_table, project_table)

    # Recursively process submanifests
    for subm in root.findall('submanifest'):
        sub_name = subm.get('manifest-name') if subm.get('manifest-name') else subm.get('name')
        sub_remote = subm.get('remote')
        sub_tag = subm.get('revision') if subm.get('revision') else release_tag
        sub_project = subm.get('project')
        if not sub_name or not sub_remote or sub_remote not in remote_table or not sub_project:
            continue
        fetch_url = remote_table[sub_remote]
        # Convert github.com to raw.githubusercontent.com for fetch_url
        if fetch_url.startswith("https://github.com"):
            fetch_url = fetch_url.replace("https://github.com", "https://raw.githubusercontent.com")
        fetch_url = fetch_url.rstrip('/')
        # Build correct submanifest URL: {remote}/{project}/{revision}/{manifest-name}
        url = f"{fetch_url}/{sub_project}/{sub_tag}/{sub_name}"
        sub_xml = fetch_manifest_xml(url)
        parse_manifest(sub_xml, url, sub_tag, processed_manifests, remote_table, project_table)

    return remote_table, project_table

def main():
    start_time = time.time()

    # Compute script directory to make all relative paths work regardless of cwd
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Read release_information.conf for manifest info
    conf_path = os.path.join(script_dir, "release_information.conf")
    release_info = {}
    log.info(f"Reading release information from {conf_path}")
    try:
        with io.open(conf_path, 'r', encoding='utf-8') as conf_file:
            for line in conf_file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    release_info[k.strip()] = v.strip()
    except Exception as e:
        log.error(f"Error reading {conf_path}: {e}")
        sys.exit(1)

    # Check required variables
    missing_vars = []
    for var in ["MANIFEST_REPO_BASE_URL", "MANIFEST_NAME", "RELEASE_VERSION", "RDKE_LAYER"]:
        if not release_info.get(var, "").strip():
            missing_vars.append(var)
    if missing_vars:
        log.error(f"The following required variables are missing or empty in Tools/release_information.conf: {', '.join(missing_vars)}")
        sys.exit(1)

    if len(sys.argv) not in (5, 6):
        log.error("Setup requirements (one time): pip install requests")
        log.error("Usage: python3 Tools/update_readme.py Tools/README_TEMPLATE.md README.md \"AUTHOR,email\" \"<TestReportUrl>\" [<FeatureListUrl>]")
        sys.exit(1)

    template_file = sys.argv[1]
    output_file = sys.argv[2]
    author = sys.argv[3]
    test_report_url = sys.argv[4]
    feature_list_url = sys.argv[5] if len(sys.argv) == 6 else ''
    feature_list_line = f"List of features: {feature_list_url}" if feature_list_url else ''

    base_url = release_info.get('MANIFEST_REPO_BASE_URL', '')
    original_base_url = base_url
    manifest_name = release_info.get('MANIFEST_NAME', '')
    if not manifest_name.endswith('.xml'):
        manifest_name += '.xml'
    release_version = release_info.get('RELEASE_VERSION', '')
    rdke_layer = release_info.get('RDKE_LAYER', '')
    valid_layers = {"Vendor", "Middleware", "Application"}
    if rdke_layer not in valid_layers:
        log.error(
            f"Invalid RDKE_LAYER '{rdke_layer}' in {conf_path}; expected one of: {', '.join(sorted(valid_layers))}"
        )
        sys.exit(1)

    component_urls_path = os.path.join(script_dir, "component_urls.conf")
    package_versions_path = os.path.join(os.path.dirname(script_dir), f"{rdke_layer}PackagesAndVersions.md")
    if not os.path.isfile(component_urls_path):
        log.error(f"Missing required file: {component_urls_path}. See Tools/UPDATE_GUIDE.md.")
        sys.exit(1)
    if not os.path.isfile(package_versions_path):
        log.error(
            f"Missing required file: {package_versions_path}. Generate it per Tools/UPDATE_GUIDE.md before running."
        )
        sys.exit(1)

    # Only convert to raw.githubusercontent.com for fetching manifests, not for README links
    fetch_base_url = base_url
    if fetch_base_url.startswith("https://github.com"):
        fetch_base_url = fetch_base_url.replace("https://github.com", "https://raw.githubusercontent.com")
    fetch_base_url = fetch_base_url.rstrip('/')

    manifest_url = f"{fetch_base_url}/{release_version}/{manifest_name}"
    xml_text = fetch_manifest_xml(manifest_url)
    try:
        remote_table, project_table = parse_manifest(xml_text, manifest_url, release_version)
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    # Format project table for README: Name | Revision/Tag Link (GitHub: link, else plain)
    project_rows = []
    seen = set()
    for proj in project_table:
        name = proj['name']
        if name in seen:
            continue
        seen.add(name)
        remote = proj['remote']
        revision = proj['revision']
        remote_url = remote_table.get(remote, '')
        # Always strip refs/tags/ for display
        display_rev = revision
        is_tag = False
        if revision.startswith('refs/tags/'):
            display_rev = revision[len('refs/tags/'):]
            is_tag = True
        link = display_rev
        # Handle GitHub links (org root or repo URL)
        org = None
        if remote_url.startswith('https://github.com/') or remote_url.startswith('https://raw.githubusercontent.com/'):
            parts = remote_url.split('/')
            if len(parts) > 3:
                org = parts[3]
            repo = proj['name']
            if org and repo:
                gh_url = f"https://github.com/{org}/{repo}"
                if not is_tag and len(display_rev) == 40 and all(c in '0123456789abcdef' for c in display_rev.lower()):
                    link = f"[{display_rev}]({gh_url}/commit/{display_rev})"
                else:
                    link = f"[{display_rev}]({gh_url}/tree/{display_rev})"
        # If Yocto, generate link
        elif 'git.yoctoproject.org' in remote_url:
            repo = name
            if len(display_rev) == 40 and all(c in '0123456789abcdef' for c in display_rev.lower()):
                link = f"[{display_rev}](https://git.yoctoproject.org/cgit/cgit.cgi/{repo}/commit/?id={display_rev})"
            else:
                link = display_rev
        project_rows.append(f"| {name} | {link} |")
    project_md = '\n'.join(project_rows)

    # Get Yocto version (from main manifest)
    tree = ET.ElementTree(ET.fromstring(COMMENT_RE.sub('', xml_text)))
    root = tree.getroot()
    yocto_elem = root.find('yocto')
    yocto_version = yocto_elem.get('version') if yocto_elem is not None and yocto_elem.get('version') else 'Kirkstone'

    # Get UTC date string
    from datetime import datetime, timezone
    gen_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    log.info(f"Reading template file: {template_file}")
    try:
        with io.open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        log.error(f"Error reading template file {template_file}: {e}")
        sys.exit(1)

    # Fill test report line if provided
    test_report_line = ''
    if test_report_url:
        test_report_line = f"Release Details: [{test_report_url}]({test_report_url})"

    # Set PACKAGE_LIST_LINE only for Vendor, Middleware, or Application layers
    if rdke_layer in ["Vendor", "Middleware", "Application"]:
        package_list_line = f"The [packages and versions]({rdke_layer}PackagesAndVersions.md) file provides the list of packages in this {rdke_layer} release."
    else:
        package_list_line = ""

    content = content.replace('<RELEASE_VERSION>', release_version)
    content = content.replace('<YOCTO_VERSION>', yocto_version)
    content = content.replace('<LAYER_TABLE>', project_md)
    content = content.replace('<RDKE_LAYER>', rdke_layer)
    content = content.replace('<BASE_URL>', original_base_url)
    content = content.replace('<PACKAGE_LIST_LINE>', package_list_line)
    content = content.replace('<FEATURE_LIST_LINE>', feature_list_line)
    content = content.replace('<GEN_DATE>', gen_date)
    content = content.replace('<AUTHOR>', author)
    content = content.replace('<TEST_REPORT_LINE>', test_report_line)

    try:
        with io.open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        log.error(f"Error writing output file {output_file}: {e}")
        sys.exit(1)
    log.info(f"Updated README written to {output_file}")

    # --- Hyperlink package versions in PackagesAndVersions.md ---
    log.info(f"Updating {rdke_layer}PackagesAndVersions.md with hyperlinks.")
    url_map = parse_component_urls_conf(component_urls_path)
    update_package_versions_md(package_versions_path, url_map)
    log.info(f"Updated {rdke_layer}PackagesAndVersions.md with hyperlinks.")
    print("Finished in {:.2f} seconds".format(time.time() - start_time))

if __name__ == "__main__":
    main()
