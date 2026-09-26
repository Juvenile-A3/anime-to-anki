local mp = require "mp"

local function seek(seconds)
    mp.commandv("seek", tostring(seconds), "exact")
end

mp.add_forced_key_binding("LEFT", "anime-small-seek-back", function()
    seek(-5)
end)

mp.add_forced_key_binding("RIGHT", "anime-small-seek-forward", function()
    seek(5)
end)