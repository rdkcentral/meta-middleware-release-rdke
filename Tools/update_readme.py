from __future__ import print_function
import sys
import io
import requests
import xml.etree.ElementTree as ET
import re


# Remove XML comments to avoid parsing commented or disabled sections
COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)


def fetch_manifest_xml(manifest_url):
    resp = requests.get(manifest_url)
    if resp.status_code != 200:
        print("Failed to fetch manifest XML from {}".format(manifest_url))
        sys.exit(1)
    return resp.text


def parse_manifest(xml_text, manifest_url, release_tag, processed_manifests=None, remote_table=None, project_table=None):
    # Remove XML comments
    xml_text = COMMENT_RE.sub('', xml_text)
    tree = ET.ElementTree(ET.fromstring(xml_text))
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

    # Build project table
    for project in root.findall('project'):
        name = project.get('name')
        remote = project.get('remote')
        revision = project.get('revision')
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
            # Use current manifest's repo URL
            fetch_url = manifest_url.rsplit('/', 2)[0]  # up to repo/tag
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
        # Build correct submanifest URL: {remote}/{project}/{revision}/{manifest-name}
        url = f"{fetch_url}/{sub_project}/{sub_tag}/{sub_name}"
        sub_xml = fetch_manifest_xml(url)
        parse_manifest(sub_xml, url, sub_tag, processed_manifests, remote_table, project_table)

    return remote_table, project_table


def main():
    if len(sys.argv) not in (8, 9):
        print("Setup requirements (one time): pip install requests")
        print("Usage: python3 Tools/update_readme.py Tools/README_TEMPLATE.md README.md <MANIFEST_REPO_BASE_URL> <MANIFEST_NAME> <RELEASE_VERSION> <RDKE_LAYER> \"AUTHOR,email\" \"[TestReportUrl]\"")
        sys.exit(1)

    template_file = sys.argv[1]
    output_file = sys.argv[2]
    base_url = sys.argv[3]
    original_base_url = base_url
    manifest_name = sys.argv[4]
    if not manifest_name.endswith('.xml'):
        manifest_name += '.xml'
    release_version = sys.argv[5]
    rdke_layer = sys.argv[6]
    author = sys.argv[7]
    test_report_url = sys.argv[8] if len(sys.argv) == 9 else ''

    # Only convert to raw.githubusercontent.com for fetching manifests, not for README links
    fetch_base_url = base_url
    if fetch_base_url.startswith("https://github.com"):
        fetch_base_url = fetch_base_url.replace("https://github.com", "https://raw.githubusercontent.com")

    manifest_url = f"{fetch_base_url}/{release_version}/{manifest_name}"
    xml_text = fetch_manifest_xml(manifest_url)
    remote_table, project_table = parse_manifest(xml_text, manifest_url, release_version)

    # Format remote table for README
    remote_rows = ["| Name | Fetch URL |"]
    for name, url in remote_table.items():
        remote_rows.append(f"| {name} | {url} |")
    remote_md = '\n'.join(remote_rows)

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
        link_type = 'plain'
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
                    link_type = 'github-commit'
                else:
                    link = f"[{display_rev}]({gh_url}/tree/{display_rev})"
                    link_type = 'github-tag'
        # If Yocto, generate link
        elif 'git.yoctoproject.org' in remote_url:
            repo = name
            if len(display_rev) == 40 and all(c in '0123456789abcdef' for c in display_rev.lower()):
                link = f"[{display_rev}](https://git.yoctoproject.org/cgit/cgit.cgi/{repo}/commit/?id={display_rev})"
                link_type = 'yocto-commit'
            else:
                link = display_rev
                link_type = 'yocto-plain'
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

    with io.open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find meta-stack-layering-support revision/tag for hyperlinking variables.md.
    meta_stacklayering_version = ''
    for proj in project_table:
        if proj['name'] == 'meta-stack-layering-support':
            tag = proj['revision']
            if tag.startswith('refs/tags/'):
                tag = tag[len('refs/tags/'):]
            meta_stacklayering_version = tag
            break

    # Fill test report line if provided
    if test_report_url:
        test_report_line = f"Test Report: [{test_report_url}]({test_report_url})"
    else:
        test_report_line = f"Test Report: Contact {author}"

    content = content.replace('<RELEASE_VERSION>', release_version)
    content = content.replace('<YOCTO_VERSION>', yocto_version)
    content = content.replace('<REMOTE_TABLE>', remote_md)
    content = content.replace('<LAYER_TABLE>', project_md)
    content = content.replace('<RDKE_LAYER>', rdke_layer)
    content = content.replace('<BASE_URL>', original_base_url)
    content = content.replace('<STACKLAYERING_VERSION>', meta_stacklayering_version)
    content = content.replace('<GEN_DATE>', gen_date)
    content = content.replace('<AUTHOR>', author)
    content = content.replace('<TEST_REPORT_LINE>', test_report_line)

    with io.open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated README written to {}".format(output_file))

if __name__ == "__main__":
    main()
