#RDKMVE-1694: Fix to remove -U option for broadcom wpa_supplicant v2.11
wpa_supplicant_conf_override() {
    local FILE="${IMAGE_ROOTFS}/lib/rdk/prepareWpaSuppConfig.sh"

    if [ -f "$FILE" ]; then
        sed -i 's/ -U//g' "$FILE"
    fi
}
ROOTFS_POSTPROCESS_COMMAND:wpa_supplicant_2_11 += "  wpa_supplicant_conf_override; "
