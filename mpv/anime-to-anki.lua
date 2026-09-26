local mp = require "mp"
local utils = require "mp.utils"
local options = require "mp.options"

local o = {
    python = "python",
    module = "anime_to_anki",
    config = "",
    key = "a",
    keep_payload = "no",
}

options.read_options(o, "anime_to_anki")

local function temp_payload_path()
    local temp = os.getenv("TEMP") or os.getenv("TMP") or "."
    local name = string.format(
        "anime-to-anki-%d-%d.json",
        os.time(),
        math.random(100000, 999999)
    )
    return utils.join_path(temp, name)
end

local function write_payload(payload)
    local path = temp_payload_path()
    local file, err = io.open(path, "wb")
    if not file then
        return nil, err
    end

    file:write(utils.format_json(payload))
    file:close()
    return path, nil
end

local function build_args(payload_path)
    local args = {
        o.python,
        "-m",
        o.module,
        "capture",
        "--payload-file",
        payload_path,
    }

    if o.config and o.config ~= "" then
        table.insert(args, "--config")
        table.insert(args, o.config)
    end

    return args
end

local function first_line(text)
    if not text then
        return ""
    end
    local line = text:gsub("\\N", "\n"):match("[^\r\n]+") or ""
    if #line > 42 then
        return line:sub(1, 42) .. "..."
    end
    return line
end

local function subtitle_path_for_id(track_id)
    if not track_id or track_id == "" or track_id == "no" then
        return nil
    end

    local tracks = mp.get_property_native("track-list", {})
    for _, track in ipairs(tracks) do
        if track.type == "sub" and tostring(track.id) == tostring(track_id) then
            return track["external-filename"] or track["filename"]
        end
    end

    return nil
end

local function capture()
    local media_path = mp.get_property("path")
    if not media_path or media_path == "" then
        mp.osd_message("Anki capture failed: no media path", 3)
        return
    end

    local payload = {
        media_path = media_path,
        working_directory = mp.get_property("working-directory"),
        media_title = mp.get_property("media-title"),
        time_pos = mp.get_property_number("time-pos"),
        duration = mp.get_property_number("duration"),
        sub_start = mp.get_property_number("sub-start"),
        sub_end = mp.get_property_number("sub-end"),
        sub_text = mp.get_property("sub-text", ""),
        secondary_sub_text = mp.get_property("secondary-sub-text", ""),
        sid = mp.get_property("sid"),
        secondary_sid = mp.get_property("secondary-sid"),
        subtitle_path = subtitle_path_for_id(mp.get_property("sid")),
        secondary_subtitle_path = subtitle_path_for_id(mp.get_property("secondary-sid")),
    }

    if (not payload.sub_text or payload.sub_text == "") and
        (not payload.secondary_sub_text or payload.secondary_sub_text == "") then
        mp.osd_message("Anki capture: no current subtitle", 2)
    end

    local payload_path, err = write_payload(payload)
    if not payload_path then
        mp.osd_message("Anki capture failed: " .. tostring(err), 4)
        return
    end

    mp.osd_message("Capturing Anki card...", 1)
    mp.command_native_async(
        {
            name = "subprocess",
            args = build_args(payload_path),
            playback_only = false,
            capture_stdout = true,
            capture_stderr = true,
        },
        function(success, result, error)
            if o.keep_payload ~= "yes" then
                os.remove(payload_path)
            end

            if not success then
                mp.osd_message("Anki capture failed: " .. tostring(error), 5)
                return
            end

            local status = result and result.status or -1
            if status == 0 then
                local decoded = utils.parse_json(result.stdout or "")
                if decoded and decoded.anki_error and decoded.anki_error ~= "" then
                    mp.osd_message("Saved locally; AnkiConnect failed", 4)
                elseif decoded and decoded.japanese and decoded.japanese ~= "" then
                    mp.osd_message("Captured: " .. first_line(decoded.japanese), 2)
                else
                    mp.osd_message("Anki card captured", 2)
                end
            else
                local message = result.stderr or result.stdout or "unknown error"
                local decoded = utils.parse_json(message)
                if decoded and decoded.error then
                    message = decoded.error
                end
                mp.osd_message("Anki capture failed: " .. first_line(message), 6)
            end
        end
    )
end

mp.add_forced_key_binding(o.key, "anime-to-anki-capture", capture)
