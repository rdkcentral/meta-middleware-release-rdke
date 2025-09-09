# How to update this README automatically

1. Generate *PackagesAndVersions.md* for the target `PACKAGE_ARCH` by building the RDKE `<RDKE_LAYER>` stack for specific ***RELEASE_VERSION*** with `DEPLOY_IPK_FEED = "1"` and `GENERATE_IPK_VERSION_DOC = "1"` in `${BUILDDIR}/conf/local.conf`. The generated file will be in `${BUILDDIR}/tmp/deploy/ipk/${PACKAGE_ARCH}/` and replace here as `<RDKE_LAYER>PackagesAndVersions.md`. See [variables.md](https://github.com/rdkcentral/meta-stack-layering-support/blob/<STACKLAYERING_VERSION>/docs/variables.md) for supported options.
2. Cross check and update the ***component_urls.conf*** for any new or missing ***component & it's url*** for the list of components in the generated `<RDKE_LAYER>PackagesAndVersions.md`. Component's ***url*** can be obtained from respective ***bitbake recipe***.
3. Update the contents of `release_information.conf` (especially `RELEASE_VERSION`, `MANIFEST_REPO_BASE_URL`, `MANIFEST_NAME`, and `RDKE_LAYER`). Then run the script from the base directory:


```sh
# Requires Python 3.x
# Setup requirements (one time): pip install requests
# RDKE_LAYER can be Vendor/Middleware/Application
# Script now supports GITHUB_API_TOKEN environment variable(optional) to reduce the GitHub API rate limit failures.
Usage: export GITHUB_API_TOKEN="Token"; python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md "AUTHOR,email" "TestReportUrl" [FeatureListUrl]
```
 - Most configuration is now read from `release_information.conf`.
 - The script will automatically update `<RDKE_LAYER>PackagesAndVersions.md` with hyperlinks for each package with the help of `component_urls.conf` provided details.
 - Adjust paths and shell syntax for your OS (Windows/Linux/Mac).
Eg (Linux Host):
```sh
python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md "ReleaseTeam, email_id" "https://example.com/test-report" "https://example.com/features"
```
