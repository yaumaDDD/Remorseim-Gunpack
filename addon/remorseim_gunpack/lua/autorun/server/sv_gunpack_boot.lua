--[[---------------------------------------------------------
	Remorseim Gunpack — sv_gunpack_boot.lua (только сервер)

	1. Регистрирует список оружия, которое принёс аддон (для категории в
	   спавн-меню и для точечных апгрейдов).
	2. Регистрирует звуки и модели, которые аддон приносит с собой
	   (см. content_manifest.json — его генерирует build/bat-скрипт).
	3. Досоздаёт отсутствующие хелперы, которые нужны новому оружию.

	ВАЖНО: аддон ничего не заменяет и не перезаписывает. Всё, что здесь
	делается — дополнение (add, not replace).
---------------------------------------------------------]]

local GP = REMORSEIM_GUNPACK
if not GP then return end

----------------------------------------------------------------
-- 1. Список оружия
----------------------------------------------------------------
GP.Weapons = {
	-- винтовки
	weapon_50beowulf = true,
	weapon_ak47 = true,
	weapon_type56 = true,
	weapon_m16a1 = true,
	weapon_m16a1_30 = true,
	weapon_nlar15 = true, -- нелетальный AR-15

	-- пистолеты-пулемёты
	weapon_mp5a5 = true,
	weapon_mp5k = true,
	weapon_mp5sd6 = true,
	weapon_mp5eod = true,
	weapon_mp5_custom = true,
	weapon_mp5sd6_custom = true,
	weapon_mp540 = true,
	weapon_ro635 = true,

	-- пулемёты
	weapon_coltlmg = true,
	weapon_m231 = true,
	weapon_m231ad = true,

	-- дробовики
	weapon_m4short = true,
	weapon_m4sport = true,
	weapon_m4tac = true,
	weapon_m870 = true,
	weapon_m870mcs = true,
	weapon_remington870_long = true,
	weapon_remington870_sawed_off = true,
	weapon_spas12_modern = true,
	weapon_spas12_short = true,
	weapon_spas12_folded = true,

	-- пистолеты
	weapon_glock17b = true,
	weapon_glock17fd = true,
	weapon_glock17lb = true,
	weapon_deagle_c = true,
	weapon_deagle_annihilator = true,
	weapon_m1911compact = true,
	weapon_m1911custom = true,
	weapon_nlglock17 = true,
	weapon_nlglock26 = true,
	weapon_revolverm500 = true,


	-- снаряжение
	weapon_ammocrate = true,
	weapon_hg_grenade_incendiary_tpik = true, -- AN M14, зажигательная
	weapon_defibrillator = true,
	weapon_midazolam = true,
	weapon_enhanced_hook = true,
	weapon_spawnmenu_pda = true,

	-- авиаудары / бомбы
	weapon_callbomber = true,
	weapon_carpetbomber = true,
	weapon_airstrike = true,
	weapon_uav = true,
}

----------------------------------------------------------------
-- 1.1 Ближний бой — отдельная ветка
----------------------------------------------------------------
-- Все свep'ы лежат на своей базе weapon_rem_melee_base и живут в отдельной
-- категории "Weapons - Remorseim Melee". Классы Z-City не переопределяются,
-- поэтому оба набора сосуществуют.
GP.MeleeWeapons = {
	weapon_rem_melee_ballistic_shield = true,
	weapon_rem_melee_bat = true,
	weapon_rem_melee_brick = true,
	weapon_rem_melee_buck200knife = true,
	weapon_rem_melee_chainsaw = true,
	weapon_rem_melee_chair_leg = true,
	weapon_rem_melee_combatknife = true,
	weapon_rem_melee_hammer = true,
	weapon_rem_melee_hatchet = true,
	weapon_rem_melee_hg_axe = true,
	weapon_rem_melee_hg_bottle = true,
	weapon_rem_melee_hg_bottlebroken = true,
	weapon_rem_melee_hg_crowbar = true,
	weapon_rem_melee_hg_crowbar_gordon = true,
	weapon_rem_melee_hg_extinguisher = true,
	weapon_rem_melee_hg_glassshard = true,
	weapon_rem_melee_hg_glassshard_taped = true,
	weapon_rem_melee_hg_machete = true,
	weapon_rem_melee_hg_mug = true,
	weapon_rem_melee_hg_shovel = true,
	weapon_rem_melee_hg_sledgehammer = true,
	weapon_rem_melee_hg_spear = true,
	weapon_rem_melee_hg_spear_knife = true,
	weapon_rem_melee_hg_spear_pro = true,
	weapon_rem_melee_hg_stunstick = true,
	weapon_rem_melee_hg_tonfa = true,
	weapon_rem_melee_leadpipe = true,
	weapon_rem_melee_metalbat = true,
	weapon_rem_melee_pan = true,
	weapon_rem_melee_pocketknife = true,
	weapon_rem_melee_ram = true,
	weapon_rem_melee_sogknife = true,
	weapon_rem_melee_table_leg = true,
}

----------------------------------------------------------------
-- 2. Ресурсы: звуки и модели, которых нет в обычном Z-City
----------------------------------------------------------------
-- Список генерирует build/build_addon.py в sv_gunpack_content.lua.
-- Если контента нет на сервере — регистрация просто ничего не сделает,
-- аддон продолжит работать (модели/звуки подтянутся из воркшопа).
if GP.Content then
	local n_snd, n_mdl, n_pcf = 0, 0, 0

	for _, snd in ipairs(GP.Content.sounds or {}) do
		resource.AddSingleFile(snd)
		n_snd = n_snd + 1
	end

	for _, mdl in ipairs(GP.Content.models or {}) do
		resource.AddSingleFile(mdl)
		n_mdl = n_mdl + 1
	end

	for _, pcf in ipairs(GP.Content.particles or {}) do
		resource.AddSingleFile(pcf)
		n_pcf = n_pcf + 1
	end

	GP.Log(string.format("content: %d sounds, %d models, %d particles", n_snd, n_mdl, n_pcf))
end

----------------------------------------------------------------
-- 3. Хелперы, которых нет в обычном Z-City
----------------------------------------------------------------
if not hg then hg = {} end

-- ent_enhanced_hook дергает hg.velocityDamage, а в обычном Z-City
-- он есть только как локальная функция внутри sv_input.lua.
if not hg.velocityDamage then
	hg.velocityDamage = function(ent, data)
		if not IsValid(ent) then return end

		local speed = (istable(data) and data.Speed) or (ent.GetVelocity and ent:GetVelocity():Length()) or 0
		if speed < 250 then return end

		local dmg = math.min(speed / 40, 25)
		local dmginfo = DamageInfo()
		dmginfo:SetDamage(dmg)
		dmginfo:SetDamageType(DMG_CLUB)
		dmginfo:SetDamagePosition(ent:GetPos())
		ent:TakeDamageInfo(dmginfo)
	end
end

-- AED (weapon_defibrillator) в Remorseim умеет запускать фибрилляцию.
-- В обычном Z-City hg.organism.StartFibrillation нет.
if SERVER and hg.organism and not hg.organism.StartFibrillation then
	hg.organism.StartFibrillation = function(org)
		if not org or org.heartstop then return end
		org.fibrillation = true
		org.fibrillationStart = CurTime()
	end
end

-- Старый вариант запуска фибрилляции (на случай, если формируем её вручную)
if SERVER and hg.organism and not hg.organism.AddCardiacStress then
	hg.organism.AddCardiacStress = function(org, amount)
		if not org or not isnumber(amount) or amount <= 0 then return 0 end
		org.arrhythmia = math.Clamp((org.arrhythmia or 0) + amount, 0, 1)
		org.heartStrain = math.Clamp((org.heartStrain or 0) + amount * 0.45, 0, 1)
		return org.arrhythmia
	end
end

-- AED из Remorseim ожидает hg.DefibReviveIncapacitated; в обычном Z-City
-- функцию оживляющую через дефибриллятор надо подставить свою.
-- (Реализация ниже — аккуратная копия поведения Z-City: поднять FakeRagdoll
--  и очистить состояние организма, если игрок ещё не мёртв окончательно.)
if SERVER and not hg.DefibReviveIncapacitated then
	hg.DefibReviveIncapacitated = function(defib, owner, ply, getTarget, uses)
		if not IsValid(defib) then return end
		if defib.AEDDropped or defib.AEDFinalized then return end

		local target = IsValid(getTarget and getTarget()) and getTarget() or nil
		if not IsValid(target) then return end

		defib.AEDFinalized = true
		defib.AEDShocked = true
		defib.AEDState = "shocked"

		local victim = IsValid(ply) and ply or target
		local org = target.organism

		if org then
			if hg.organism and hg.organism.Clear then
				hg.organism.Clear(org)
			else
				org.otrub = false
				org.needotrub = false
				org.incapacitated = false
				org.heartstop = false
				org.fibrillation = false
				org.heartbeat = 70
				org.pulse = 70
				org.consciousness = 1
				org.pain = 0
				org.bleed = 0
				org.wounds = {}
			end

			org.deathStateEnd = nil
			org.deathStateKilled = nil
			org.needotrub = false
			org.needfake = false
			org.defibDeathGrace = CurTime() + 45 -- окошко, чтобы не умереть сразу
		end

		timer.Simple(1, function()
			if not IsValid(target) then return end
			if org and (org.otrub or org.incapacitated) then return end
			if IsValid(target.FakeRagdoll) and hg.FakeUp then
				hg.FakeUp(target, true)
			end
		end)

		if IsValid(victim) and victim.IsPlayer and victim:IsPlayer() then
			victim.fullsend = true
		end
	end
end

----------------------------------------------------------------
-- 4. Категория в спавн-меню
----------------------------------------------------------------
hook.Add("PopulateContent", "remorseim_gunpack_populate", function()
	-- оружие Remorseim уже разложено по своим SWEP.Category
	-- ("Weapons - Assault Rifles", "Weapons - Melee" и т.д.) — так оно
	-- встаёт рядом с обычным арсеналом Z-City, а не отдельной свалкой.
	GP.Log("PopulateContent hook ready")
end)

GP.Log("server boot ok, version " .. tostring(GP.Version))
