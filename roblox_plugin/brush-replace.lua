local InsertService = game:GetService("InsertService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local toolbar = plugin:CreateToolbar("Blender Map Builder")
local button = toolbar:CreateButton(
	"Replace Brushes", 
	"Replaces Blender placeholders with their Toolbox models", 
	"rbxassetid://10656736270" -- Feel free to change this icon
)

button.Click:Connect(function()
	ChangeHistoryService:SetWaypoint("Before Brush Swap")
	
	local placeholdersCount = 0
	
	for _, inst in ipairs(workspace:GetDescendants()) do
		if inst:IsA("BasePart") and inst:GetAttribute("IsBlenderBrush") then
			
			local assetIdStr = inst:GetAttribute("BrushAssetId")
			local assetId = tonumber(assetIdStr)
			
			if assetId then
				print("Replacing brush with Asset ID: " .. assetId)
				
				-- 1. Download the Asset
				local success, loadedModel = pcall(function()
					return InsertService:LoadAsset(assetId)
				end)
				
				if success and loadedModel then
					-- LoadAsset returns a Model containing the actual asset
					local actualAsset = loadedModel:GetChildren()[1] 
					
					if actualAsset and actualAsset:IsA("Model") then
						actualAsset.Parent = inst.Parent
						
						-- 2. Match the CFrame (Position and Rotation)
						actualAsset:PivotTo(inst.CFrame)
						
						-- 3. Match the Scale 
						-- (We compare the Blender bounding box height to the Model's height)
						local targetExtents = actualAsset:GetExtentsSize()
						if targetExtents.Y > 0 then
							local scaleFactor = inst.Size.Y / targetExtents.Y
							actualAsset:ScaleTo(scaleFactor)
						end
						
						-- 4. Delete the invisible placeholder
						inst:Destroy()
						placeholdersCount += 1
					end
					
					loadedModel:Destroy()
				else
					warn("Failed to load asset ID: " .. tostring(assetId))
				end
			end
		end
	end
	
	print("Successfully swapped " .. placeholdersCount .. " brushes!")
	ChangeHistoryService:SetWaypoint("After Brush Swap")
end)local InsertService = game:GetService("InsertService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local toolbar = plugin:CreateToolbar("Blender Map Builder")
local button = toolbar:CreateButton(
	"Replace Brushes", 
	"Replaces Blender placeholders with their Toolbox models", 
	"rbxassetid://10656736270" -- Feel free to change this icon
)

button.Click:Connect(function()
	ChangeHistoryService:SetWaypoint("Before Brush Swap")
	
	local placeholdersCount = 0
	
	for _, inst in ipairs(workspace:GetDescendants()) do
		if inst:IsA("BasePart") and inst:GetAttribute("IsBlenderBrush") then
			
			local assetIdStr = inst:GetAttribute("BrushAssetId")
			local assetId = tonumber(assetIdStr)
			
			if assetId then
				print("Replacing brush with Asset ID: " .. assetId)
				
				-- 1. Download the Asset
				local success, loadedModel = pcall(function()
					return InsertService:LoadAsset(assetId)
				end)
				
				if success and loadedModel then
					-- LoadAsset returns a Model containing the actual asset
					local actualAsset = loadedModel:GetChildren()[1] 
					
					if actualAsset and actualAsset:IsA("Model") then
						actualAsset.Parent = inst.Parent
						
						-- 2. Match the CFrame (Position and Rotation)
						actualAsset:PivotTo(inst.CFrame)
						
						-- 3. Match the Scale 
						-- (We compare the Blender bounding box height to the Model's height)
						local targetExtents = actualAsset:GetExtentsSize()
						if targetExtents.Y > 0 then
							local scaleFactor = inst.Size.Y / targetExtents.Y
							actualAsset:ScaleTo(scaleFactor)
						end
						
						-- 4. Delete the invisible placeholder
						inst:Destroy()
						placeholdersCount += 1
					end
					
					loadedModel:Destroy()
				else
					warn("Failed to load asset ID: " .. tostring(assetId))
				end
			end
		end
	end
	
	print("Successfully swapped " .. placeholdersCount .. " brushes!")
	ChangeHistoryService:SetWaypoint("After Brush Swap")
end)