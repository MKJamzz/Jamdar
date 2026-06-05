import psutil


def list_drives() -> list[dict]:
    """Return list of {label, path} for available output locations."""
    drives = []
    seen = set()

    for part in psutil.disk_partitions(all=False):
        mountpoint = part.mountpoint
        if mountpoint in seen:
            continue
        seen.add(mountpoint)

        # Include root and /home always; include /media /run/media /mnt for removable
        is_removable = any(mountpoint.startswith(p) for p in ("/media", "/run/media", "/mnt"))
        is_home = mountpoint in ("/", "/home")

        if not (is_removable or is_home):
            continue

        try:
            usage = psutil.disk_usage(mountpoint)
            free_gb = usage.free / 1024 ** 3
        except PermissionError:
            continue

        if is_removable:
            label = f"Drive: {mountpoint.split('/')[-1]}  ({free_gb:.1f} GB free)"
        else:
            label = f"Home ({free_gb:.1f} GB free)" if mountpoint == "/" else f"{mountpoint} ({free_gb:.1f} GB free)"

        drives.append({"label": label, "path": mountpoint})

    return drives
