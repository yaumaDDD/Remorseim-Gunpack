--[[---------------------------------------------------------
	Remorseim Gunpack — sh_remorseim_gunpack.lua
	Общий (клиент + сервер) слой аддона.

	ЧТО ЭТО
	-------
	Отдельный аддон, который ДОБАВЛЯЕТ в обычный Z-City оружие и melee-swep'ы
	из архива Remorseim, которых в нём нет. Ничего не заменяет: файлы Z-City
	не перезаписываются, базовые классы (weapon_melee, homigrad_base,
	weapon_m4super, weapon_revolver2 и т.д.) используются как есть.

	ЗАЧЕМ НУЖЕН ЭТОТ ФАЙЛ
	----------------------
	Часть оружия Remorseim написана под более новую (форкнутую) версию баз,
	которая лежит внутри самого Remorseim. Ставить её в Z-City нельзя — она
	перезапишет и сломает весь остальной арсенал. Поэтому здесь точечно
	докидываются только отсутствующие методы и калибры, и только если их нет.
---------------------------------------------------------]]

REMORSEIM_GUNPACK = REMORSEIM_GUNPACK or {}
local GP = REMORSEIM_GUNPACK

GP.Version = "1.0.0"
GP.Weapons = GP.Weapons or {}   -- заполняется в sv_gunpack_boot.lua

----------------------------------------------------------------
-- Логирование
----------------------------------------------------------------
if SERVER then
	GP.cvVerbose = CreateConVar("remorseim_gunpack_verbose", "0", FCVAR_ARCHIVE,
		"Подробный лог Remorseim Gunpack в консоль сервера")
end

function GP.Log(...)
	if not GP.cvVerbose or not GP.cvVerbose:GetBool() then return end
	print("[Remorseim Gunpack]", ...)
end

----------------------------------------------------------------
-- 1. Недостающие методы базового melee-оружия
--    (в обычном Z-City их нет, они появились в форке Remorseim)
----------------------------------------------------------------

local function AddMissing(SWEP, name, fn)
	if SWEP[name] == nil then
		SWEP[name] = fn
		GP.Log("patched weapon_melee:" .. name)
	end
end

function GP.PatchMelee(SWEP)
	if not SWEP then return end

	-- Смещение левой руки (LHIK) при блоке/самопорезе.
	-- Нужно M7 Bayonet: у него прописаны SelfHarmLeftPos/SelfHarmLeftAng.
	AddMissing(SWEP, "GetLHIKStateOffset", function(self)
		local owner = self:GetOwner()
		if not IsValid(owner) then return vector_origin, angle_zero end

		if self.Canselfharm and self.IsSelfHarming and self:IsSelfHarming() then
			return self.SelfHarmLeftPos or self.LHIKSelfHarmPos or vector_origin,
				self.SelfHarmLeftAng or self.LHIKSelfHarmAng or angle_zero
		end

		if self.CanSuicide and owner.suiciding then
			return self.LHIKSuicidePos or vector_origin, self.LHIKSuicideAng or angle_zero
		end

		if self.GetBlocking and self:GetBlocking() then
			return self.LHIKBlockPos or vector_origin, self.LHIKBlockAng or angle_zero
		end

		return vector_origin, angle_zero
	end)

	-- «Игрок сейчас режет себя». В обычном Z-City есть только owner.suiciding,
	-- флага selfharming нет.
	AddMissing(SWEP, "IsSelfHarming", function(self)
		local owner = self:GetOwner()
		if not IsValid(owner) then return false end
		if SERVER then return owner.selfharming == true end
		return owner:GetNWBool("selfharming", false)
	end)

	-- Тряска камеры при самопорезе (косметика)
	AddMissing(SWEP, "GetSelfHarmShake", function(self, curve)
		curve = curve or 1
		local t = CurTime() * 38
		local posAmount = (self.SelfHarmShakePos or 0.35) * curve
		local angAmount = (self.SelfHarmShakeAng or 5) * curve
		return Vector(math.sin(t * 1.17), math.cos(t * 1.43), math.sin(t * 1.71)) * posAmount,
			Angle(math.sin(t * 1.31), math.cos(t * 1.57), math.sin(t * 1.89)) * angAmount
	end)

	-- Название метода из Remorseim (используется в weapon_combatknife)
	AddMissing(SWEP, "GetSelfHarmCutLocal", function(self)
		return self.SelfHarmCutLocalPos or vector_origin, self.SelfHarmCutLocalAng or angle_zero
	end)

	-- Комбо-система: у цепной пилы и биты прописаны ComboEnabled/ComboDamageMul1..3
	AddMissing(SWEP, "ResetCombo", function(self)
		self.ComboCount = 0
		self.ComboExpire = 0
		self.ComboAppliedThisAttack = nil
	end)

	AddMissing(SWEP, "GetComboDamageMul", function(self)
		if (self.ComboExpire or 0) < CurTime() then self.ComboCount = 0 end
		local step = math.Clamp((self.ComboCount or 0) + 1, 1, 3)
		if step == 2 then return self.ComboDamageMul2 or 1, step end
		if step == 3 then return self.ComboDamageMul3 or 1, step end
		return self.ComboDamageMul1 or 1, step
	end)

	AddMissing(SWEP, "ApplyComboDamage", function(self, dmg)
		if not self.ComboEnabled then return dmg end
		local mul = self.GetComboDamageMul and self:GetComboDamageMul() or 1
		return dmg * mul
	end)

	-- Цепная пила вызывает это из Holster/OnRemove
	AddMissing(SWEP, "CancelChargeAttack", function(self, playIdle)
		if not self.Charging and self.ReleasedChargeDamageMul == nil then return end
		self.Charging = nil
		self.ChargeStart = nil
		self.ReleasedChargeDamageMul = nil
		self.ReleasedChargeBoneMul = nil
		if playIdle and self.PlayAnim then self:PlayAnim("idle", 10, true) end
	end)

	-- Кулдаун повторного удара по той же цели (используется битой)
	AddMissing(SWEP, "IsHitCooldownTarget", function(self, ent)
		if not self.HitCooldownEnabled then return false end
		self.HitCooldownTargets = self.HitCooldownTargets or {}
		local t = self.HitCooldownTargets[ent]
		return t ~= nil and t > CurTime()
	end)

	AddMissing(SWEP, "ApplyHitCooldown", function(self, ent)
		if not self.HitCooldownEnabled then return end
		self.HitCooldownTargets = self.HitCooldownTargets or {}
		self.HitCooldownTargets[ent] = CurTime() + (self.HitCooldown or 0.5)
	end)

end

----------------------------------------------------------------
-- 2. Калибры, которых нет в обычном Z-City
----------------------------------------------------------------

local matPistol = Material("vgui/hud/bullets/low_caliber.png")
local matRifle = Material("vgui/hud/bullets/high_caliber.png")

local function TracerSettings(hs, len, w, speed, nospin)
	return {
		TracerBody = Material("particle/fire"),
		TracerTail = Material("effects/laser_tracer"),
		TracerHeadSize = hs,
		TracerLength = len,
		TracerWidth = w,
		TracerColor = Color(255, 237, 155),
		TracerTPoint1 = 0.25,
		TracerTPoint2 = 1,
		TracerSpeed = speed,
		NoSpin = nospin,
	}
end

-- Ключ (технический) -> параметры. name — то, что видит игрок.
GP.AmmoTypes = {
	[".500s&wmagnum"] = {
		name = ".500 S&W Magnum", allowed = true, dmgtype = DMG_BULLET, tracer = TRACER_LINE,
		plydmg = 0, npcdmg = 0, force = 150, maxcarry = 100, minsplash = 6, maxsplash = 6,
		TracerSetings = TracerSettings(5, 35, 1.5, 25000),
		BulletSettings = { Damage = 60, Force = 60, Penetration = 16, Shell = "50ae", Speed = 600, Diameter = 12.7, Mass = 26, Icon = matPistol },
	},
	["12.7x43"] = {
		name = "12.7x43 Beowulf", allowed = true, dmgtype = DMG_BULLET, tracer = TRACER_LINE,
		plydmg = 0, npcdmg = 0, force = 220, maxcarry = 120, minsplash = 11, maxsplash = 11,
		TracerSetings = TracerSettings(5, 75, 2, 25000),
		BulletSettings = { Damage = 51, Force = 51, Penetration = 17, Shell = "762x51", Speed = 980, Diameter = 6.8, Mass = 8, Icon = matRifle },
	},
	["9x19rubber"] = {
		name = "9x19 Rubber", allowed = true, dmgtype = DMG_CLUB, tracer = TRACER_LINE,
		plydmg = 0, npcdmg = 0, force = 100, maxcarry = 80, minsplash = 0, maxsplash = 0,
		TracerSetings = TracerSettings(1, 5, 1, 6000, true),
		BulletSettings = { Damage = 25, Force = 25, Penetration = 1, Shell = "9x19", Speed = 352, Diameter = 11.19, Mass = 10, Icon = matPistol },
	},
	["5.56rubber"] = {
		name = "5.56x45 Rubber", allowed = true, dmgtype = DMG_CLUB, tracer = TRACER_LINE,
		plydmg = 0, npcdmg = 0, force = 100, maxcarry = 120, minsplash = 0, maxsplash = 0,
		TracerSetings = TracerSettings(2, 155, 2, 25000, true),
		BulletSettings = { Damage = 14, Force = 14, Penetration = 1, Shell = "556x45", Speed = 890, Diameter = 5.56, Mass = 4, Icon = matRifle },
	},
}

GP.AmmoEntities = {
	[".500s&wmagnum"] = { Icon = "vgui/hud/50fmj.png", Material = "models/hmcd_ammobox_22", Color = Color(255, 255, 125), Scale = 1, Count = 20 },
	["12.7x43"] = { Icon = "vgui/hud/bullets/high_caliber.png", Material = "models/hmcd_ammobox_792", Color = Color(218, 165, 32), Scale = 1, Count = 40 },
	["9x19rubber"] = { Icon = "vgui/hud/bullets/low_caliber.png", Material = "models/hmcd_ammobox_9", Color = Color(218, 165, 32), Scale = 0.9, Count = 60 },
	["5.56rubber"] = { Icon = "vgui/hud/bullets/high_caliber.png", Material = "models/hmcd_ammobox_9", Color = Color(218, 165, 32), Scale = 0.9, Count = 60 },
}

-- Калибры, которые есть в Z-City, но отсутствуют в SWEP.AmmoTypes2 базового
-- homigrad_base. Без записи self.AmmoTypes становится nil и часть систем
-- (смена типа патрона, HUD) падает.
GP.AmmoTypes2Entries = {
	["12.7x43 Beowulf"] = { [1] = { "12.7x43 Beowulf" } },
	[".500 S&W Magnum"] = { [1] = { ".500 S&W Magnum" } },
	[".40 SW"] = { [1] = { ".40 SW" } },
	["9x19 Rubber"] = { [1] = { "9x19 Rubber" } },
	["5.56x45 Rubber"] = { [1] = { "5.56x45 Rubber" } },
}

local ammoDone = false

function GP.RegisterAmmoTypes()
	if ammoDone then return true end
	if not hg or not hg.ammotypes then return false end -- Z-City ещё не загрузился

	hg.ammotypeshuy = hg.ammotypeshuy or {}
	hg.ammotypesallowed = hg.ammotypesallowed or {}
	hg.ammoents = hg.ammoents or {}

	for key, tbl in pairs(GP.AmmoTypes) do
		-- Дописываем lookup по отображаемому имени (нужен всегда)
		if not hg.ammotypeshuy[tbl.name] then
			local huy = hg.ammotypeshuy[key] or table.Copy(tbl)
			huy.name = key
			hg.ammotypeshuy[tbl.name] = huy
			if huy.allowed then hg.ammotypesallowed[tbl.name] = huy end
		end

		if not hg.ammotypes[key] then
			local bs = tbl.BulletSettings
			if bs and bs.Diameter and bs.Speed and bs.Speed > 0 then
				-- тот же расчёт сопротивления воздуха, что в sh_ammostuff.lua
				bs.AirResistanceCoef = 8 / (1.2255 * (bs.Speed ^ 2) * math.pi * ((bs.Diameter / 1000) ^ 2))
			end

			hg.ammotypes[key] = tbl

			local huy = hg.ammotypeshuy[tbl.name]
			if huy then huy.name = key end

			local ent = GP.AmmoEntities[key] or {}
			hg.ammoents[key] = ent

			game.AddAmmoType(tbl)

			if not ent.noentity then
				if CLIENT then language.Add(tbl.name .. "_ammo", tbl.name) end

				local ammoent = {
					Base = "ammo_base",
					PrintName = tbl.name,
					Category = "ZCity Ammo",
					Spawnable = true,
					AmmoCount = ent.Count or 30,
					AmmoType = tbl.name,
					Model = ent.Model or "models/props_lab/box01a.mdl",
					ModelMaterial = ent.Material or "",
					ModelScale = ent.Scale or 1,
					Color = ent.Color or color_white,
					IconOverride = ent.Icon or "vgui/hud/bullets/high_caliber.png",
				}

				if scripted_ents.GetStored("ent_ammo_" .. key) == nil then
					scripted_ents.Register(ammoent, "ent_ammo_" .. key)
				end
			end

			GP.Log("ammo type registered:", key, "->", tbl.name)
		end
	end

	game.BuildAmmoTypes()
	ammoDone = true
	return true
end

local ammo2Done = false

function GP.RegisterAmmoTypes2()
	if ammo2Done then return true end
	local base = weapons.GetStored("homigrad_base")
	if not base or not base.AmmoTypes2 then return false end

	for name, tbl in pairs(GP.AmmoTypes2Entries) do
		if not base.AmmoTypes2[name] then
			base.AmmoTypes2[name] = tbl
			GP.Log("AmmoTypes2 entry added:", name)
		end
	end

	ammo2Done = true
	return true
end

----------------------------------------------------------------
-- 3. Точечные апгрейды наших SWEP'ов
----------------------------------------------------------------

local function UpgradeWeapon(SWEP, class)
	if not SWEP then return end

	-- .40 SW у MP5/40: в AmmoTypes2 нет записи — подкладываем свою.
	if SWEP.Primary and SWEP.Primary.Ammo == ".40 SW" then
		SWEP.AmmoTypes2 = SWEP.AmmoTypes2 or { [".40 SW"] = { [1] = { ".40 SW" } } }
	end
end
GP.UpgradeWeapon = UpgradeWeapon

----------------------------------------------------------------
-- 4. Точка входа
----------------------------------------------------------------

function GP.Apply()
	GP.PatchMelee(weapons.GetStored("weapon_melee"))
	GP.RegisterAmmoTypes()
	GP.RegisterAmmoTypes2()

	for class in pairs(GP.Weapons) do
		UpgradeWeapon(weapons.GetStored(class), class)
	end

	GP._applied = true
end

hook.Add("InitPostEntity", "remorseim_gunpack_init", function()
	GP.Apply()
	GP.Log("applied on InitPostEntity")
end)

-- Резерв: если InitPostEntity уже прошёл (например аддон включили в
-- работающей игре или на клиенте подключились позже), догоняем по таймеру.
timer.Simple(1, function()
	if not GP._applied then
		GP.Apply()
		GP.Log("applied by fallback timer")
	end
end)
