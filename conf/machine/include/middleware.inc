# To support layered ipk generation

DISTRO = "rdk"

MIDDLEWARE_ARCH = "${MACHINE}-middleware"
PACKAGE_EXTRA_ARCHS:append = " ${MIDDLEWARE_ARCH}"

# Set RDKE_MIDDLEWARE_ARTIFACTS_BASE_URL according to the IPK feed hosting format.
# Below url is dummy which need to be updated to point to actual host.
# Protocol can be either "file://" for local feed or remote eg: "https://".
RDKE_MIDDLEWARE_ARTIFACTS_BASE_URL ??= "file://user/home/rdke-release"
RELEASE_NUM = "2.7.0"

MW_IPK_PATH = "${MIDDLEWARE_ARCH}/${RELEASE_NUM}/ipks"
MW_IPK_SERVER_PATH = "${RDKE_MIDDLEWARE_ARTIFACTS_BASE_URL}/${MW_IPK_PATH}"

IPK_FEED_URIS += " \ 
                ${MIDDLEWARE_ARCH}##${MW_IPK_SERVER_PATH} "
