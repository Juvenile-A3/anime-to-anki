local mp = require "mp"
local utils = require "mp.utils"
local msg = require "mp.msg"

local function sanitize_filename(value)
    local name = tostring(value or "screenshot")
    name = name:gsub("[\\/:*?\"<>|]", "_")
    name = name:gsub("%s+", " ")
    name = name:gsub("^%s+", ""):gsub("%s+$", "")
    name = name:gsub("%.$", "")
    if name == "" then
        return "screenshot"
    end
    return name
end

local function time_label(seconds)
    seconds = tonumber(seconds) or 0
    if seconds < 0 then
        seconds = 0
    end

    local total_ms = math.floor(seconds * 1000 + 0.5)
    local ms = total_ms % 1000
    local total_seconds = math.floor(total_ms / 1000)
    local s = total_seconds % 60
    local total_minutes = math.floor(total_seconds / 60)
    local m = total_minutes % 60
    local h = math.floor(total_minutes / 60)
    return string.format("%02d-%02d-%02d-%03d", h, m, s, ms)
end

local function screenshot_extension()
    local format = mp.get_property("screenshot-format", "png")
    if format == "jpeg" then
        return "jpg"
    end
    return format or "png"
end

local function next_available_path(directory, stem, extension)
    local candidate = utils.join_path(directory, stem .. "." .. extension)
    if not utils.file_info(candidate) then
        return candidate
    end

    local index = 2
    while true do
        candidate = utils.join_path(directory, string.format("%s_%02d.%s", stem, index, extension))
        if not utils.file_info(candidate) then
            return candidate
        end
        index = index + 1
    end
end

local function copy_image_to_clipboard(path)
    local helper = utils.join_path(mp.get_script_directory(), "anime-screenshot-copy.ps1")

    mp.command_native_async(
        {
            name = "subprocess",
            args = {
                "powershell.exe",
                "-NoProfile",
                "-STA",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                helper,
                "-ImagePath",
                path,
            },
            playback_only = false,
            capture_stdout = true,
            capture_stderr = true,
        },
        function(success, result, error)
            local status = result and result.status or -1
            if success and status == 0 then
                mp.osd_message("Screenshot saved and copied", 2)
            else
                local detail = error or (result and result.stderr) or "unknown error"
                msg.error("Clipboard copy failed: " .. tostring(detail))
                mp.osd_message("Screenshot saved, but clipboard copy failed", 3)
            end
        end
    )
end

local function take_screenshot()
    local directory = mp.get_property("screenshot-directory", "")
    if directory == "" then
        directory = mp.get_property("working-directory", ".")
    end

    local filename = mp.get_property("filename/no-ext") or mp.get_property("filename") or "screenshot"
    local stem = sanitize_filename(filename) .. "-" .. time_label(mp.get_property_number("time-pos", 0))
    local path = next_available_path(directory, stem, screenshot_extension())

    local ok, err = pcall(mp.commandv, "screenshot-to-file", path, "subtitles")
    if ok then
        mp.osd_message("Screenshot: " .. path, 1)
        mp.add_timeout(0.1, function()
            copy_image_to_clipboard(path)
        end)
    else
        mp.osd_message("Screenshot failed: " .. tostring(err), 3)
    end
end

mp.add_forced_key_binding("s", "anime-screenshot", take_screenshot)
