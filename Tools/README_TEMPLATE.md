
# RDKE <RDKE_LAYER> Layer <RELEASE_VERSION> Release Note

| Summary       | Content |
|---------------|---------|
| Manifest URL  | <BASE_URL> |
| Release Tag   | [<RELEASE_VERSION>](<BASE_URL>/releases/tag/<RELEASE_VERSION>) |
| Yocto Version | <YOCTO_VERSION> |
| Date          | <GEN_DATE> |
| Author        | <AUTHOR> |


### <RDKE_LAYER> Release Details
The [Packages And Versions](VendorPackagesAndVersions.md) file provides a table listing <RDKE_LAYER>-supplied package names and their versions of [<RDKE_LAYER> Release <RELEASE_VERSION>](<BASE_URL>/releases/tag/<RELEASE_VERSION>) which aligns with below layer combination.

For a comprehensive list of changes, updates, and release history, refer to the [Changelog](CHANGELOG.md).

<TEST_REPORT_LINE>

| Layer Name | Current Revision/Tag |
|------------|-------------------|
<LAYER_TABLE>

For RDKE <RDKE_LAYER> layer specific build instructions, refer [this](<BASE_URL>/blob/<RELEASE_VERSION>/README.md)

## License Details
This project is distributed under the terms outlined in the associated [License](LICENSE) and [Notice](NOTICE) files. Please review these files for detailed information.

---

#### How to update this README automatically

1. Generate `PackagesAndVersions.md` for the target `PACKAGE_ARCH` by building the <RDKE_LAYER> stack for `<RELEASE_VERSION>` with `DEPLOY_IPK_FEED = "1"` and `GENERATE_IPK_VERSION_DOC = "1"` in `${BUILDDIR}/conf/local.conf`. The generated file will be in `${BUILDDIR}/tmp/deploy/ipk/${PACKAGE_ARCH}/`. See [variables.md](https://github.com/rdkcentral/meta-stack-layering-support/blob/<STACKLAYERING_VERSION>/docs/variables.md) for supported options.
2. Run `Tools/update_readme.py` script from base directory to generate the final README. Note: change to match Host's shell conventions and filesystem path syntax(Windows/Linux/Mac).
```sh
# Requires Python 3.x
# Setup requirements (one time): pip install requests
Usage: python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md <MANIFEST_REPO_BASE_URL> <MANIFEST_NAME> <RELEASE_VERSION> <RDKE_LAYER> "AUTHOR,email" "[TestReportUrl(optional)]"
```
- Replace the arguments with the actual release/tag/commit values matching the release.

Eg (Linux Host):
```sh
python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md https://github.com/rdkcentral/vendor-manifest-raspberrypi rdke-raspberrypi.xml 4.5.1 Vendor "ReleaseTeam, email_id" "https://example.com/test-report"
```

---
