# Quantum Care Integration for Orchid Continuum
# Integrated quantum-enhanced orchid care simulation

from flask import request, jsonify, render_template
import math

def vpd_kpa(temp_c: float, rh: float) -> float:
    """Calculate Vapor Pressure Deficit"""
    es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (rh / 100.0)
    return max(es - ea, 0.0)

def ppfd_from_lux(lux: float, light_type: str = "white_led") -> float:
    """Convert lux to PPFD"""
    factor = 0.018 if light_type == "white_led" else 0.015
    return lux * factor

def register_quantum_care_routes(app):
    """Register quantum care routes with Flask app"""
    
    @app.route('/api/quantum/simulate-care', methods=['POST'])
    def simulate_care():
        """Quantum-enhanced orchid care simulation"""
        data = request.get_json()
        
        # Parse input
        temp_c = float(data.get('temp_c', 22))
        rh = float(data.get('rh', 65))
        lux = data.get('lux', 15000)
        quantum = data.get('quantum', False)
        species = data.get('scientific_name', '')
        
        # Calculate PPFD and VPD
        ppfd = ppfd_from_lux(lux, "white_led") if lux else 120.0
        vpd = vpd_kpa(temp_c, rh)
        
        # Base care parameters
        target_ppfd = min(max(ppfd, 80.0), 250.0)
        target_rh_low, target_rh_high = 55.0, 75.0
        watering_days = [2, 5]
        stress = max(min((vpd - 1.2) / 1.0, 1.0), 0.0)
        
        # Quantum corrections
        if quantum:
            # Default quantum parameters
            k_coh = 0.12 if "CAM" in species else 0.08
            alpha, beta = 0.15, 0.10
            bump = 1.0 + alpha * k_coh
            penalty = 1.0 - beta * stress
            target_ppfd = target_ppfd * bump * penalty
            target_rh_low = max(50.0, target_rh_low - 3.0)
            target_rh_high = min(80.0, target_rh_high + 3.0)
            watering_days = [3, 6]
        
        return jsonify({
            'vpd_kpa': round(vpd, 3),
            'target_ppfd': round(target_ppfd, 1),
            'target_rh': [round(target_rh_low), round(target_rh_high)],
            'watering_days': watering_days,
            'notes': 'Care targets with optional quantum correction (coherence bump & stress penalty).',
            'uncertainty': 'Demo ranges; calibrate to ΦPSII/Fv/Fm as data accrues.'
        })

    @app.route('/api/quantum/simulate-cam', methods=['POST'])
    def simulate_cam():
        """CAM photosynthesis simulation"""
        data = request.get_json()
        
        noct_temp_c = float(data.get('noct_temp_c', 22))
        noct_rh = float(data.get('noct_rh', 65))
        quantum = data.get('quantum', False)
        
        base_swing = max(10.0 * (noct_rh/70.0) * (22.0 / max(noct_temp_c, 10.0)), 2.0)
        
        if quantum:
            gamma = 0.12
            tau_tun_ps = 2.0  # Default quantum tunneling time
            base_swing *= (1.0 + gamma * (tau_tun_ps / 10.0))
        
        lo = round(base_swing * 0.85, 2)
        hi = round(base_swing * 1.15, 2)
        
        return jsonify({
            'expected_ta_swing': [lo, hi],
            'phase_schedule': {
                'Phase I': 'Late night CO₂ fixation (PEPc) → malate storage',
                'Phase II': 'Dawn transition; mixed PEPc/Rubisco',
                'Phase III': 'Daytime decarboxylation; stomata closed',
                'Phase IV': 'Dusk transition; stomata reopening'
            },
            'sensitivity': {
                'dTA_dRH': round(base_swing * 0.01, 4),
                'dTA_dT': round(-base_swing * 0.02, 4)
            },
            'uncertainty': 'Demo; refine with species TA logs + nocturnal traces.'
        })

    @app.route('/quantum-care-widget')
    def quantum_care_widget():
        """Quantum Care Widget Interface"""
        return render_template('quantum_care_widget.html')
        
    @app.route('/api/quantum/status')
    def quantum_status():
        """Get quantum care system status"""
        return jsonify({
            'status': 'operational',
            'version': '1.0.0',
            'features': ['care_simulation', 'cam_analysis', 'quantum_corrections'],
            'endpoints': [
                '/api/quantum/simulate-care',
                '/api/quantum/simulate-cam',
                '/quantum-care-widget'
            ]
        })