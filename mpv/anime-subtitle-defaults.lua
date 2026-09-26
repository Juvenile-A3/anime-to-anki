local mp = require "mp"

local selected_for_path = nil
local timer = nil

local function b(values)
    local chars = {}
    for _, value in ipairs(values) do
        chars[#chars + 1] = string.char(value)
    end
    return table.concat(chars)
end

local U = {
    jian = b({0xE7, 0xAE, 0x80}),
    jian_trad = b({0xE7, 0xB0, 0xA1}),
    ti = b({0xE4, 0xBD, 0x93}),
    ti_trad = b({0xE9, 0xAB, 0x94}),
    zhong = b({0xE4, 0xB8, 0xAD}),
    ri = b({0xE6, 0x97, 0xA5}),
    wen = b({0xE6, 0x96, 0x87}),
    yu_s = b({0xE8, 0xAF, 0xAD}),
    yu_t = b({0xE8, 0xAA, 0x9E}),
    shuang = b({0xE5, 0x8F, 0x8C}),
    shuang_trad = b({0xE9, 0x9B, 0x99}),
    fan = b({0xE7, 0xB9, 0x81}),
    nei = b({0xE5, 0x86, 0x85}),
    feng = b({0xE5, 0xB0, 0x81}),
}

local function lower(value)
    return string.lower(tostring(value or ""))
end

local function track_label(track)
    return lower(table.concat({
        track.lang or "",
        track.title or "",
        track["external-filename"] or "",
        track.filename or "",
    }, " "))
end

local function contains_any(text, needles)
    for _, needle in ipairs(needles) do
        if text:find(needle, 1, true) then
            return true
        end
    end
    return false
end

local simplified_tokens = {
    "zh-cn", "zh_cn", "zh-hans", "zh_hans", "chs", "sc",
    "simplified", "gb", U.jian, U.jian_trad, U.jian .. U.ti,
    U.jian_trad .. U.ti_trad, U.jian .. U.zhong, U.nei .. U.feng .. U.jian,
}

local chinese_tokens = {
    "chi", "zho", "zh", "cn", "chinese", U.zhong .. U.wen, U.zhong,
}

local traditional_tokens = {
    "zh-tw", "zh_tw", "zh-hant", "zh_hant", "cht", "tc",
    "traditional", U.fan, U.fan .. U.ti, U.fan .. U.ti_trad,
}

local japanese_tokens = {
    "jpn", "jp", "ja", "japanese", U.ri .. U.wen,
    U.ri .. U.yu_s, U.ri .. U.yu_t, U.ri,
}

local bilingual_tokens = {
    "jpsc", "jp-sc", "jp_sc", "jpn-chs", "jpn_chs", "chs-jpn", "chs_jpn",
    "chi_jpn", "chi-jpn", "jpn_chi", "jpn-chi", "bilingual",
    U.shuang .. U.yu_s, U.shuang_trad .. U.yu_t,
    U.jian .. U.ri, U.jian_trad .. U.ri,
    U.ri .. U.jian, U.ri .. U.jian_trad,
    U.zhong .. U.ri, U.ri .. U.zhong,
}

local function score_simplified(track)
    local label = track_label(track)
    local score = 0
    if contains_any(label, simplified_tokens) then score = score + 100 end
    if contains_any(label, chinese_tokens) then score = score + 20 end
    if contains_any(label, traditional_tokens) then score = score - 80 end
    if track.external then score = score + 1 end
    return score
end

local function score_japanese(track)
    local label = track_label(track)
    local score = 0
    if contains_any(label, japanese_tokens) then score = score + 100 end
    if track.external then score = score + 1 end
    return score
end

local function is_bilingual(track)
    local label = track_label(track)
    return contains_any(label, bilingual_tokens)
        or (score_simplified(track) >= 100 and score_japanese(track) >= 100)
end

local function best_track(tracks, scorer, forbidden_id)
    local best = nil
    local best_score = 0
    for _, track in ipairs(tracks) do
        if track.type == "sub" and tostring(track.id) ~= tostring(forbidden_id or "") then
            local score = scorer(track)
            if score > best_score then
                best = track
                best_score = score
            end
        end
    end
    return best
end

local function select_subtitles()
    local path = mp.get_property("path", "")
    if path == "" or selected_for_path == path then
        return
    end

    local tracks = mp.get_property_native("track-list", {})
    local bilingual = best_track(tracks, function(track)
        return is_bilingual(track) and 1000 or 0
    end)

    if bilingual then
        mp.set_property("sid", tostring(bilingual.id))
        mp.set_property("secondary-sid", "no")
        selected_for_path = path
        mp.osd_message("Subtitles: bilingual", 1)
        return
    end

    local primary = best_track(tracks, score_simplified)
    local secondary = best_track(tracks, score_japanese, primary and primary.id or nil)

    if primary then
        mp.set_property("sid", tostring(primary.id))
        if secondary then
            mp.set_property("secondary-sid", tostring(secondary.id))
            mp.osd_message("Subtitles: Simplified Chinese + Japanese", 1)
        else
            mp.set_property("secondary-sid", "no")
            mp.osd_message("Subtitles: Simplified Chinese", 1)
        end
        selected_for_path = path
    elseif secondary then
        mp.set_property("sid", tostring(secondary.id))
        mp.set_property("secondary-sid", "no")
        selected_for_path = path
        mp.osd_message("Subtitles: Japanese", 1)
    end
end

local function schedule_select()
    if timer then
        timer:kill()
    end
    timer = mp.add_timeout(0.5, select_subtitles)
end

mp.register_event("file-loaded", function()
    selected_for_path = nil
    schedule_select()
end)

mp.observe_property("track-list/count", "number", function()
    if not selected_for_path then
        schedule_select()
    end
end)