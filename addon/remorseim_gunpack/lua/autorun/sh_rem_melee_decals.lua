--[[--------------------------------------------------------------------------
	Remorseim Gunpack :: синяки и капли от ударов ближнего боя

	Ближний бой Remorseim ставит на жертве не только кровь, но и синяки
	(bruise decals). В Z-City этого нет вообще: там util.Decal только кровавый.

	Чтобы не тащить в аддон весь homigrad/sh_bloody_decals.lua из Remorseim
	(это была бы подмена поведения Z-City), здесь только то, что реально нужно
	своей ветке ближнего боя:

		* свои decal-имена Bruise.Rem1..Rem4 — чужие имена не занимаем;
		* своя сетевая строка bruise_decal_rem;
		* серверный хелпер hg.ApplyBruiseTo для совместимости с логикой Remorseim.

	Всё остальное (кровь, AddDecalToEnt, bloody_decal_1) остаётся штатным
	Z-City и не дублируется.
----------------------------------------------------------------------------]]

if SERVER then
	util.AddNetworkString("bruise_decal_rem")

	local BRUISE_MATS = { "One", "Two", "Three", "Four" }

	-- Регистрируем decal-имена один раз. Префикс Rem — чтобы ни при каких
	-- условиях не столкнуться с Z-City или другими аддонами.
	local bruiseNames = {}
	for i = 1, #BRUISE_MATS do
		local name = "Bruise.Rem" .. i
		bruiseNames[i] = name
		game.AddDecal(name, "bruises/bruise" .. BRUISE_MATS[i])
		list.Add("PaintMaterials", name)
	end

	hg = hg or {}

	-- Совместимость с Remorseim: некоторые свep'ы (щит, руки) зовут это напрямую.
	if not hg.ApplyBruiseTo then
		function hg.ApplyBruiseTo(ent, victim, hitPos, hitNormal)
			if not IsValid(ent) then return end
			if not victim or not victim:IsValid() then return end
			if not hitPos or not hitNormal then return end

			local idx = math.random(#bruiseNames)

			net.Start("bruise_decal_rem")
				net.WriteEntity(ent)
				net.WriteEntity(victim)
				net.WriteUInt(idx, 4)
				net.WriteVector(hitPos)
				net.WriteVector(hitNormal)
			net.SendPVS(hitPos)
		end
	end

	return
end

-- --------------------------------------------------------------------------
-- Клиент
-- --------------------------------------------------------------------------

local bruiseSize = CreateClientConVar(
	"hg_rem_bruise_size", "0.04", true, false,
	"Размер синяка от удара ближнего боя (units)", 0.01, 5
)

net.Receive("bruise_decal_rem", function()
	local ent = net.ReadEntity()
	local victim = net.ReadEntity()
	local idx = net.ReadUInt(4)
	local pos = net.ReadVector()
	local normal = net.ReadVector()

	if not IsValid(ent) or not pos or not normal then return end

	local mat = Material(util.DecalMaterial("Bruise.Rem" .. idx))
	if not mat then return end

	local s = bruiseSize:GetFloat()
	local col = Color(255, 255, 255, math.random(80, 180))

	util.DecalEx(mat, ent, pos + normal, normal, col, s, s)

	if IsValid(victim) and victim ~= ent then
		util.DecalEx(mat, victim, pos + normal, normal, col, s, s)
	end
end)
