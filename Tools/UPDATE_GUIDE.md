# How to update this README automatically

1. Generate `PackagesAndVersions.md` for the target `PACKAGE_ARCH` by building the <RDKE_LAYER> stack for `<RELEASE_VERSION>` with `DEPLOY_IPK_FEED = "1"` and `GENERATE_IPK_VERSION_DOC = "1"` in `${BUILDDIR}/conf/local.conf`. The generated file will be in `${BUILDDIR}/tmp/deploy/ipk/${PACKAGE_ARCH}/` and replace here as `<RDKE_LAYER>PackagesAndVersions.md`. See [variables.md](https://github.com/rdkcentral/meta-stack-layering-support/blob/<STACKLAYERING_VERSION>/docs/variables.md) for supported options.
2. Run `Tools/update_readme.py` script from base directory to generate the final README. Note: change to match Host's shell conventions and filesystem path syntax (Windows/Linux/Mac).

```sh
# Requires Python 3.x
# Setup requirements (one time): pip install requests
# RDKE_LAYER can be Vendor/Middleware/Application
Usage: python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md <MANIFEST_REPO_BASE_URL> <MANIFEST_NAME> <RELEASE_VERSION> <RDKE_LAYER> "AUTHOR,email" "TestReportUrl" [FeatureListUrl]
```
- Replace the arguments with the actual release/tag/commit values matching the release.

Eg (Linux Host):
```sh
python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md https://github.com/rdkcentral/vendor-manifest-raspberrypi rdke-raspberrypi.xml 4.5.1 Middleware "ReleaseTeam, email_id" "https://example.com/test-report" "https://example.com/features"
```
