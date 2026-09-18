-- Keep short reference tables and complete workout instructions together in PDF.
-- The filter is configured only for PDF, leaving HTML and EPUB flow unchanged.
local function reserve(lines)
  return pandoc.RawBlock('latex', '\\Needspace{' .. lines .. '\\baselineskip}')
end

function Header(header)
  local lines = {
    ['easy-recovery'] = 34,
    ['first-workout-week'] = 24,
    ['transition-week'] = 30,
    ['rest-day-week'] = 24,
    ['standard-week'] = 24,
    ['larger-week'] = 24,
    ['session-cards'] = 16,
    ['first-session'] = 28,
    ['session-a'] = 32,
    ['session-b'] = 32,
    ['session-c'] = 32,
    ['marathon-week'] = 24,
    ['speed-workstridesstrength'] = 26,
  }
  local title = pandoc.utils.stringify(header.content)
  if title == 'Choose the example closest to your current routine' then
    return {reserve(24), header}
  elseif title == 'Change one thing at a time' then
    return {reserve(34), header}
  end
  if lines[header.identifier] then
    return {reserve(lines[header.identifier]), header}
  end
end

function Table(tbl)
  local heading = pandoc.utils.stringify(tbl.head)
  local lines = 20
  if heading:match('What you want to change') then
    lines = 32
  elseif heading:match('Tool') then
    lines = 22
  elseif heading:match('Day') and heading:match('Quality') then
    lines = 14
  end
  return {reserve(lines), tbl}
end
