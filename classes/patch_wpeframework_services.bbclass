# RDKECOREMW-919: Workaround to fix wpeframework-services.target systemd services startup issue
wpeframework_services_patch(){
    if [ -f "${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target" ]; then
        sed -i "s/wpeframework-cloudstore.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-analytics.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-runtimemanager.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-appmanager.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-lifecyclemanager.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-packagemanager.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
        sed -i "s/wpeframework-storagemanager.service//g" ${IMAGE_ROOTFS}/lib/systemd/system/wpeframework-services.target
    fi
}
ROOTFS_POSTPROCESS_COMMAND += "wpeframework_services_patch; "
