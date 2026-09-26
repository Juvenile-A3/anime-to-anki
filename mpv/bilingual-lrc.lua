-- Merge simultaneous LRC lines in memory; leave the source lyrics untouched.
local mp = require 'mp'
local busy, ready = false, false
local converted = {}

local function stamp(ms)
    ms = math.max(0, math.floor(ms + 0.5))
    return string.format('%02d:%02d:%02d,%03d', math.floor(ms / 3600000),
        math.floor(ms / 60000) % 60, math.floor(ms / 1000) % 60, ms % 1000)
end

local function convert(data, duration)
    -- Only process UTF-8/plain LRC. Leave UTF-16 and enhanced karaoke to mpv.
    if data:find('\0', 1, true) or data:find('<%d+:%d+%.%d+>') then return end
    data = data:gsub('^\239\187\191', ''):gsub('\r\n', '\n'):gsub('\r', '\n')
    local groups, times = {}, {}
    local offset = tonumber(data:match('%[offset:%s*([%+%-]?%d+)%s*%]')) or 0
    local duplicate = false
    for line in (data .. '\n'):gmatch('(.-)\n') do
        local stamps, rest = {}, line
        while true do
            local minutes, seconds, fraction, tail = rest:match('^%[(%d+):(%d+)[%.:](%d+)%](.*)$')
            if not minutes then
                minutes, seconds, tail = rest:match('^%[(%d+):(%d+)%](.*)$')
                fraction = '0'
            end
            if not minutes then break end
            stamps[#stamps + 1] = tonumber(minutes) * 60000 + tonumber(seconds) * 1000
                + math.floor(tonumber('0.' .. fraction) * 1000 + 0.5) - offset
            rest = tail
        end
        for _, time in ipairs(stamps) do
            if not groups[time] then
                groups[time] = {}
                times[#times + 1] = time
            end
            if rest:match('%S') then
                if #groups[time] > 0 then duplicate = true end
                groups[time][#groups[time] + 1] = rest
            end
        end
    end
    if not duplicate then return end
    table.sort(times)
    local cues = {}
    for i, time in ipairs(times) do
        local finish = times[i + 1] or (duration and duration * 1000) or (time + 10000)
        if finish > math.max(0, time) and #groups[time] > 0 then
            cues[#cues + 1] = string.format('%d\n%s --> %s\n%s\n', #cues + 1,
                stamp(time), stamp(finish), table.concat(groups[time], '\n'))
        end
    end
    if #cues > 0 then return table.concat(cues, '\n') end
end

local function repair_selected()
    if busy or not ready then return end
    local sid = mp.get_property_number('sid')
    if not sid then return end
    local tracks = mp.get_property_native('track-list', {})
    local track
    for _, candidate in ipairs(tracks) do
        if candidate.type == 'sub' and candidate.id == sid then track = candidate end
    end
    if not track or not track.external then return end
    local path = track['external-filename'] or ''
    if not path:lower():match('%.lrc$') or path:find('://', 1, true) then return end
    if converted[path] then
        for _, candidate in ipairs(tracks) do
            if candidate.type == 'sub' and candidate.id == converted[path] then
                mp.set_property_number('sid', candidate.id)
                return
            end
        end
        converted[path] = nil
    end
    local file = io.open(path, 'rb')
    if not file then return end
    local data = file:read(4 * 1024 * 1024 + 1)
    file:close()
    if not data or #data > 4 * 1024 * 1024 then return end
    local srt = convert(data, mp.get_property_number('duration'))
    if not srt then return end
    busy = true
    local ok, err = mp.commandv('sub-add', 'memory://' .. srt, 'select',
        'LRC bilingual (merged lines)', track.lang or '')
    if ok then
        converted[path] = mp.get_property_number('sid')
        mp.msg.info('Merged simultaneous LRC lines for ' .. path)
    else
        mp.msg.warn('Could not load merged LRC: ' .. tostring(err))
    end
    busy = false
end

mp.register_event('start-file', function()
    ready, busy, converted = false, false, {}
end)
mp.register_event('file-loaded', function()
    ready = true
    repair_selected()
end)
mp.register_event('end-file', function() ready = false end)
mp.observe_property('sid', 'number', repair_selected)
mp.observe_property('track-list/count', 'number', repair_selected)
