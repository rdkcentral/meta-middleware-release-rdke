# To support layered ipk generation

DISTRO = "rdk"

MIDDLEWARE_ARCH = "${MACHINE}-middleware"
PACKAGE_EXTRA_ARCHS:append = " ${MIDDLEWARE_ARCH}"

## Uncomment and set RDK_ARTIFACTS_BASE_URL according to the IPK feed hosting format.
## Protocol can be either "file://" for local feed or remote eg: "https://".
## Expected hosting path as per below config:
##      "file://home/user/rdke-release-feeds/${MACHINE}-middleware/2.7.0/ipks"

#RDK_ARTIFACTS_BASE_URL ?? = "file://home/user/rdke-release-feeds/"

RELEASE_NUM = "2.7.0"
MW_IPK_PATH = "${MIDDLEWARE_ARCH}/${RELEASE_NUM}/ipks"
MW_IPK_SERVER_PATH = "${RDK_ARTIFACTS_BASE_URL}/${MW_IPK_PATH}"

IPK_FEED_URIS += " \ 
                ${MIDDLEWARE_ARCH}##${MW_IPK_SERVER_PATH} "
