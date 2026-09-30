-- Keep short reference tables together in PDF.
-- HTML and EPUB retain their normal flow.
function Blocks(blocks)
  local result = pandoc.List()
  for _, block in ipairs(blocks) do
    if block.t == 'Table' then
      local rows = 0
      for _, body in ipairs(block.bodies) do
        rows = rows + #body.body
      end
      local space = pandoc.RawBlock('latex', '\\Needspace{' .. (rows + 7) .. '\\baselineskip}')
      -- The original interval tables follow a label inside a list item.
      -- Reserve room before that label so it stays with its table.
      if #result > 0 and (result[#result].t == 'Para' or result[#result].t == 'Plain') then
        local label = result:remove(#result)
        result:insert(space)
        result:insert(label)
      else
        result:insert(space)
      end
    end
    result:insert(block)
  end
  return result
end
