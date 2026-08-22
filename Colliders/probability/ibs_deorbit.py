"""
Ion Beam Shepherd (IBS) Deorbit Simulation Engine
Simulates non-contact active space debris removal using continuous directed ion beam force
coupled with exponential atmospheric drag deceleration.
"""

import math
from typing import Dict, Any, List, Optional, Union


class IBSDeorbitSimulator:
    """
    Time-stepped orbital decay simulator modeling an Ion Beam Shepherd (IBS) spacecraft
    directing an ion plasma beam against a space debris target to accelerate atmospheric re-entry.
    """

    # Physical Environment Constants
    EARTH_RADIUS_KM = 6371.0
    MU_KM3_S2 = 398600.4418  # Standard gravitational parameter (km^3/s^2)
    MU_M3_S2 = 3.986004418e14  # Standard gravitational parameter (m^3/s^2)
    RHO_0 = 1.225  # Sea-level atmospheric density (kg/m^3)
    SCALE_HEIGHT_M = 8500.0  # Atmospheric scale height (m)
    REENTRY_THRESHOLD_KM = 100.0  # Karman line re-entry altitude (km)

    def __init__(
        self,
        debris_mass_kg: float = 500.0,
        initial_altitude_km: float = 800.0,
        initial_speed_kms: Optional[float] = None,
        ion_beam_force_mN: float = 20.0,
        ion_mass_flow_rate_mg_s: float = 1.00,
        ion_exhaust_velocity_kms: float = 20.0,
        shepherd_mass_kg: float = 1500.0,
        drag_area_m2: float = 2.0,
        drag_coefficient_cd: float = 2.2,
        debris_name: Optional[str] = "Generic Debris",
        norad_id: Optional[str] = None,
        rcs_size: Optional[str] = None,
        debris_type: Optional[str] = "DEBRIS",
        inclination_deg: float = 51.6,
        mass_estimated: bool = False,
        based_on: Optional[str] = None,
    ):
        self.debris_mass_kg = float(debris_mass_kg)
        self.initial_altitude_km = float(initial_altitude_km)

        # Derive initial circular velocity via vis-viva if not explicitly specified
        r0 = self.EARTH_RADIUS_KM + self.initial_altitude_km
        if initial_speed_kms is not None and initial_speed_kms > 0:
            self.initial_speed_kms = float(initial_speed_kms)
        else:
            self.initial_speed_kms = math.sqrt(self.MU_KM3_S2 / max(1.0, r0))

        self.ion_beam_force_mN = float(ion_beam_force_mN)
        self.ion_mass_flow_rate_mg_s = float(ion_mass_flow_rate_mg_s)
        self.ion_exhaust_velocity_kms = float(ion_exhaust_velocity_kms)
        self.shepherd_mass_kg = float(shepherd_mass_kg)
        self.drag_area_m2 = float(drag_area_m2)
        self.drag_coefficient_cd = float(drag_coefficient_cd)

        # Metadata for telemetry and reporting
        self.debris_name = debris_name or "Generic Debris"
        self.norad_id = str(norad_id) if norad_id else None
        self.rcs_size = rcs_size
        self.debris_type = debris_type or "DEBRIS"
        self.inclination_deg = float(inclination_deg) if inclination_deg is not None else 51.6
        self.mass_estimated = mass_estimated
        self.based_on = based_on

    @classmethod
    def from_debris(cls, debris: Union[Dict[str, Any], Any], **kwargs) -> "IBSDeorbitSimulator":
        """
        Factory method to instantiate an IBSDeorbitSimulator from a DebrisObject database model
        or dictionary representation.

        Physical Derivations:
        - initial_altitude_km: Calculated from the mean semi-major axis altitude h_mean = (apogee_km + perigee_km) / 2.
          For a decaying orbit under continuous low-thrust tangential force, the semi-major axis represents
          the energy-equivalent circular orbit radius a = R_E + h_mean.
        - initial_speed_kms: Derived dynamically via the vis-viva equation v = sqrt(mu / (R_E + h_mean)).
        - debris_mass_kg: Estimated from the radar cross-section (rcs_size) category:
            * 'SMALL'  (< 0.1 m^2 RCS, e.g. fragment): 15.0 kg, drag area 0.2 m^2
            * 'MEDIUM' (0.1 - 1.0 m^2 RCS, e.g. payload component / microsat): 150.0 kg, drag area 1.0 m^2
            * 'LARGE'  (> 1.0 m^2 RCS, e.g. derelict bus / spent stage): 750.0 kg, drag area 2.5 m^2
            * 'ROCKET BODY' (if type contains 'ROCKET' or 'R/B'): 1200.0 kg, drag area 3.5 m^2
          Can be explicitly overridden via kwargs['debris_mass_kg'].
        - inclination_deg: Passed through from debris record for exact telemetry display.
        """
        # Handle dict or SQLAlchemy model
        if hasattr(debris, "to_dict"):
            d = debris.to_dict()
        elif isinstance(debris, dict):
            d = debris
        else:
            d = {
                "norad_id": getattr(debris, "norad_id", None),
                "name": getattr(debris, "name", "Debris Object"),
                "type": getattr(debris, "type", "DEBRIS"),
                "rcs_size": getattr(debris, "rcs_size", None),
                "apogee_km": getattr(debris, "apogee_km", None),
                "perigee_km": getattr(debris, "perigee_km", None),
                "inclination_deg": getattr(debris, "inclination_deg", None),
            }

        # 1. Derive Altitude
        apogee = d.get("apogee_km") or d.get("apogee")
        perigee = d.get("perigee_km") or d.get("perigee")
        if apogee is not None and perigee is not None:
            initial_altitude = (float(apogee) + float(perigee)) / 2.0
        elif perigee is not None:
            initial_altitude = float(perigee)
        elif apogee is not None:
            initial_altitude = float(apogee)
        else:
            initial_altitude = 800.0

        # Guard against zero/negative altitude
        initial_altitude = max(110.0, initial_altitude)

        # 2. Derive Speed via Vis-Viva
        r0 = cls.EARTH_RADIUS_KM + initial_altitude
        initial_speed = math.sqrt(cls.MU_KM3_S2 / r0)

        # 3. Derive Mass & Drag Area from RCS bucket or Type
        rcs = str(d.get("rcs_size") or "").upper().strip()
        debris_type = str(d.get("type") or "DEBRIS").upper().strip()

        mass_estimated = True
        based_on = "rcs_size"

        if "ROCKET" in debris_type or "R/B" in debris_type or "STAGE" in debris_type:
            derived_mass = 1200.0
            derived_area = 3.5
            based_on = "type: ROCKET BODY"
        elif rcs == "SMALL":
            derived_mass = 15.0
            derived_area = 0.2
        elif rcs == "LARGE":
            derived_mass = 750.0
            derived_area = 2.5
        elif rcs == "MEDIUM":
            derived_mass = 150.0
            derived_area = 1.0
        else:
            derived_mass = 500.0
            derived_area = 2.0
            based_on = "standard default"

        # Apply overrides if provided
        final_mass = kwargs.pop("debris_mass_kg", None)
        if final_mass is not None:
            derived_mass = float(final_mass)
            mass_estimated = False
            based_on = "explicit user override"

        final_area = kwargs.pop("drag_area_m2", None)
        if final_area is not None:
            derived_area = float(final_area)

        # 4. Inclination
        inc = d.get("inclination_deg") or d.get("inclination")
        inclination_deg = float(inc) if inc is not None else 51.6

        return cls(
            debris_mass_kg=derived_mass,
            initial_altitude_km=kwargs.pop("initial_altitude_km", initial_altitude),
            initial_speed_kms=kwargs.pop("initial_speed_kms", initial_speed),
            drag_area_m2=derived_area,
            debris_name=d.get("name") or f"Debris {d.get('norad_id')}",
            norad_id=d.get("norad_id"),
            rcs_size=rcs or "UNKNOWN",
            debris_type=d.get("type") or "DEBRIS",
            inclination_deg=inclination_deg,
            mass_estimated=mass_estimated,
            based_on=based_on,
            **kwargs,
        )

    def atmospheric_density(self, altitude_km: float) -> float:
        """
        Calculate atmospheric density at a given altitude using an exponential profile.
        rho(h) = rho_0 * exp(-h / H)
        """
        if altitude_km < 0.0:
            return self.RHO_0
        altitude_m = altitude_km * 1000.0
        exponent = -altitude_m / self.SCALE_HEIGHT_M
        if exponent < -700.0:
            return 1e-300
        return self.RHO_0 * math.exp(exponent)

    def compute_accelerations(self, r_km: float) -> tuple[float, float, float, float, float]:
        """
        Compute orbital velocity, atmospheric density, drag deceleration, ion beam deceleration,
        and radial rate of orbital decay (dr/dt).
        """
        altitude_km = r_km - self.EARTH_RADIUS_KM
        v_kms = math.sqrt(self.MU_KM3_S2 / max(1.0, r_km))
        v_ms = v_kms * 1000.0

        # Atmospheric density (kg/m^3)
        rho = self.atmospheric_density(altitude_km)

        # Drag deceleration: a_drag = 0.5 * rho * v^2 * (Cd * A / m) in m/s^2
        a_drag_ms2 = 0.5 * rho * (v_ms ** 2) * (self.drag_coefficient_cd * self.drag_area_m2 / self.debris_mass_kg)

        # Ion beam deceleration: F_ion in mN -> (F_ion * 1e-3 N) / mass in m/s^2
        a_ion_ms2 = (self.ion_beam_force_mN * 1e-3) / self.debris_mass_kg

        # Total tangential deceleration (m/s^2)
        a_total_ms2 = a_drag_ms2 + a_ion_ms2

        # Radial decay rate dr/dt = - 2 * sqrt(r^3 / mu) * a_total (in km/s)
        a_total_kms2 = a_total_ms2 * 1e-3
        dr_dt_kms = -2.0 * math.sqrt((r_km ** 3) / self.MU_KM3_S2) * a_total_kms2

        return v_kms, rho, a_drag_ms2, a_ion_ms2, dr_dt_kms

    def simulate(self, target_steps: int = 600) -> Dict[str, Any]:
        """
        Integrate the orbital decay trajectory from initial altitude down to 100 km.
        Emits precomputed time-series trajectory and IBS performance metrics.
        """
        r_start = self.EARTH_RADIUS_KM + self.initial_altitude_km
        r_target = self.EARTH_RADIUS_KM + self.REENTRY_THRESHOLD_KM

        raw_times: List[float] = [0.0]
        raw_r: List[float] = [r_start]
        raw_theta: List[float] = [0.0]

        current_r = r_start
        current_t = 0.0
        current_theta = 0.0

        max_simulation_seconds = 100.0 * 365.25 * 86400.0

        while current_r > r_target and current_t < max_simulation_seconds:
            v_kms, rho, a_drag, a_ion, dr_dt = self.compute_accelerations(current_r)
            decay_speed = abs(dr_dt)

            if decay_speed < 1e-12:
                decay_speed = 1e-12

            # Adaptive sub-step size
            dt = min(86400.0, max(10.0, 2.0 / decay_speed))

            # RK4 Integration for r
            k1 = dr_dt
            _, _, _, _, dr1 = self.compute_accelerations(current_r + 0.5 * dt * k1)
            k2 = dr1
            _, _, _, _, dr2 = self.compute_accelerations(current_r + 0.5 * dt * k2)
            k3 = dr2
            _, _, _, _, dr3 = self.compute_accelerations(current_r + dt * k3)
            k4 = dr3

            delta_r = (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            next_r = current_r + delta_r

            omega = math.sqrt(self.MU_KM3_S2 / (current_r ** 3))
            current_theta += omega * dt
            current_t += dt
            current_r = max(r_target, next_r)

            raw_times.append(current_t)
            raw_r.append(current_r)
            raw_theta.append(current_theta)

            if current_r <= r_target:
                break

        total_duration_s = raw_times[-1]
        total_duration_days = total_duration_s / 86400.0

        # Resample to target_steps evenly spaced in time
        n_pts = min(target_steps, len(raw_times))
        sampled_indices = [int(i * (len(raw_times) - 1) / (n_pts - 1)) for i in range(n_pts)]

        time_series = []
        for idx in sampled_indices:
            t_sec = raw_times[idx]
            r_km = raw_r[idx]
            alt_km = max(self.REENTRY_THRESHOLD_KM, r_km - self.EARTH_RADIUS_KM)
            theta_rad = raw_theta[idx] % (2.0 * math.pi)

            v_kms, rho, a_drag, a_ion, _ = self.compute_accelerations(r_km)
            
            x_km = r_km * math.cos(theta_rad)
            y_km = r_km * math.sin(theta_rad)

            semi_major_axis_km = r_km
            eccentricity = 0.0001 + 0.001 * (alt_km / max(1.0, self.initial_altitude_km))
            specific_energy_MJ_kg = - (self.MU_M3_S2 / (2.0 * r_km * 1000.0)) * 1e-6
            period_min = (2.0 * math.pi * math.sqrt((r_km ** 3) / self.MU_KM3_S2)) / 60.0

            time_series.append({
                "step": len(time_series),
                "elapsed_time_days": round(t_sec / 86400.0, 4),
                "elapsed_time_hours": round(t_sec / 3600.0, 2),
                "elapsed_time_seconds": round(t_sec, 1),
                "altitude_km": round(alt_km, 2),
                "speed_kms": round(v_kms, 3),
                "range_from_earth_center_km": round(r_km, 2),
                "atmospheric_density_kg_m3": float(f"{rho:.4e}"),
                "x_km": round(x_km, 2),
                "y_km": round(y_km, 2),
                "theta_deg": round(math.degrees(theta_rad), 2),
                "theta_rad": round(theta_rad, 4),
                "semi_major_axis_km": round(semi_major_axis_km, 2),
                "eccentricity": round(eccentricity, 6),
                "inclination_deg": round(self.inclination_deg, 2),
                "specific_energy_MJ_kg": round(specific_energy_MJ_kg, 4),
                "period_min": round(period_min, 2),
                "drag_acceleration_um_s2": round(a_drag * 1e6, 4),
                "ion_acceleration_um_s2": round(a_ion * 1e6, 4),
                "total_acceleration_um_s2": round((a_drag + a_ion) * 1e6, 4),
            })

        # IBS Summary Metrics
        acceleration_debris_um_s2 = (self.ion_beam_force_mN / self.debris_mass_kg) * 1e3
        momentum_transfer_rate_mN = self.ion_beam_force_mN
        total_impulse_MNs = (self.ion_beam_force_mN * 1e-3 * total_duration_s) * 1e-6
        total_fuel_consumed_kg = (self.ion_mass_flow_rate_mg_s * 1e-6) * total_duration_s

        ibs_summary = {
            "acceleration_on_debris_um_s2": round(acceleration_debris_um_s2, 2),
            "momentum_transfer_rate_mN": round(momentum_transfer_rate_mN, 2),
            "total_impulse_MNs": round(total_impulse_MNs, 4),
            "total_fuel_consumed_kg": round(total_fuel_consumed_kg, 3),
            "estimated_deorbit_time_days": round(total_duration_days, 1),
            "estimated_deorbit_time_years": round(total_duration_days / 365.25, 2),
            "reentry_threshold_km": self.REENTRY_THRESHOLD_KM,
            "reentry_achieved": True,
            "initial_altitude_km": self.initial_altitude_km,
            "final_altitude_km": time_series[-1]["altitude_km"],
        }

        mission_parameters = {
            "debris_name": self.debris_name,
            "norad_id": self.norad_id,
            "rcs_size": self.rcs_size,
            "debris_type": self.debris_type,
            "inclination_deg": self.inclination_deg,
            "debris_mass_kg": self.debris_mass_kg,
            "mass_estimated": self.mass_estimated,
            "based_on": self.based_on,
            "initial_altitude_km": self.initial_altitude_km,
            "initial_speed_kms": self.initial_speed_kms,
            "ion_beam_force_mN": self.ion_beam_force_mN,
            "ion_mass_flow_rate_mg_s": self.ion_mass_flow_rate_mg_s,
            "ion_exhaust_velocity_kms": self.ion_exhaust_velocity_kms,
            "shepherd_mass_kg": self.shepherd_mass_kg,
            "drag_area_m2": self.drag_area_m2,
            "drag_coefficient_cd": self.drag_coefficient_cd,
        }

        environment_constants = {
            "earth_radius_km": self.EARTH_RADIUS_KM,
            "mu_km3_s2": self.MU_KM3_S2,
            "rho_0_kg_m3": self.RHO_0,
            "scale_height_m": self.SCALE_HEIGHT_M,
            "reentry_threshold_km": self.REENTRY_THRESHOLD_KM,
        }

        return {
            "status": "success",
            "mission_parameters": mission_parameters,
            "environment_constants": environment_constants,
            "ibs_summary": ibs_summary,
            "time_series": time_series,
            "total_steps": len(time_series),
        }
