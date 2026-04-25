export const ZONE_NAMES = {
  1:'North Chennai', 2:'Perambur', 3:'T. Nagar', 4:'Anna Nagar',
  5:'Adyar', 6:'Kodambakkam', 7:'Velachery', 8:'Mylapore',
  9:'Tambaram', 10:'Porur', 11:'Chromepet', 12:'Ambattur',
  13:'Avadi', 14:'Sholinganallur', 15:'Perungudi', 16:'Guindy',
  17:'Nungambakkam', 18:'Egmore', 19:'Thiruvottiyur', 20:'Manali',
}

export const SEASON_DISPLAY = {
  SW_monsoon: { en:'SW Monsoon',   ta:'தென்மேற்கு பருவமழை', hi:'दक्षिण-पश्चिम मानसून' },
  NE_monsoon: { en:'NE Monsoon',   ta:'வடகிழக்கு பருவமழை',  hi:'उत्तर-पूर्व मानसून' },
  heat:       { en:'Summer Heat',  ta:'கோடை வெப்பம்',        hi:'गर्मी का मौसम' },
  dry:        { en:'Dry Season',   ta:'வறண்ட காலம்',          hi:'शुष्क मौसम' },
}

export const TIER_DISPLAY = {
  high:   { en:'High (Tier 3)',   ta:'அதிக ஆபத்து (நிலை 3)',    hi:'उच्च जोखिम (स्तर 3)',    color:'#DC2626' },
  medium: { en:'Medium (Tier 2)', ta:'மிதமான ஆபத்து (நிலை 2)', hi:'मध्यम जोखिम (स्तर 2)',   color:'#D97706' },
  low:    { en:'Low (Tier 1)',    ta:'குறைந்த ஆபத்து (நிலை 1)', hi:'कम जोखिम (स्तर 1)',     color:'#059669' },
}

export const STATUS_DISPLAY = {
  waiting:   { en:'Waiting Period', ta:'காத்திருப்பு காலம்', hi:'प्रतीक्षा अवधि', color:'#6B7280' },
  active:    { en:'Active',          ta:'செயலில்',             hi:'सक्रिय',          color:'#059669' },
  suspended: { en:'Suspended',       ta:'நிறுத்தப்பட்டது',     hi:'निलंबित',          color:'#DC2626' },
  lapsed:    { en:'Lapsed',          ta:'காலாவதியானது',        hi:'समाप्त',           color:'#9CA3AF' },
}

export const TRIGGER_DISPLAY = {
  heavy_rain:          { en:'Heavy Rain',          ta:'கனமழை',                   hi:'भारी बारिश',               icon:'🌧️' },
  very_heavy_rain:     { en:'Very Heavy Rain',      ta:'மிகவும் கனமழை',           hi:'अत्यधिक भारी बारिश',       icon:'⛈️' },
  extreme_heavy_rain:  { en:'Extreme Rain',         ta:'அதிக கனமழை',              hi:'अत्यंत भारी बारिश',        icon:'🌊' },
  severe_heatwave:     { en:'Severe Heatwave',      ta:'கடுமையான வெப்ப அலை',     hi:'गंभीर लू',                  icon:'🔥' },
  severe_aqi:          { en:'Severe Air Pollution', ta:'கடுமையான காற்று மாசு',    hi:'गंभीर वायु प्रदूषण',       icon:'😷' },
  platform_suspension: { en:'Platform Suspended',   ta:'தளம் நிறுத்தப்பட்டது',   hi:'प्लेटफ़ॉर्म निलंबित',      icon:'📵' },
}

export const PINCODE_ZONE_MAP = {
  600042: { zone: 7, tier: 'high',   name: 'Velachery' },
  600040: { zone: 4, tier: 'medium', name: 'Anna Nagar' },
  600045: { zone: 9, tier: 'medium', name: 'Tambaram' },
  600017: { zone: 3, tier: 'medium', name: 'T. Nagar' },
  600020: { zone: 5, tier: 'low',    name: 'Adyar' },
  600044: { zone:11, tier: 'medium', name: 'Chromepet' },
  600028: { zone: 6, tier: 'low',    name: 'Kodambakkam' },
  600024: { zone: 8, tier: 'high',   name: 'Mylapore' },
  600041: { zone: 5, tier: 'low',    name: 'Adyar' },
  600001: { zone:18, tier: 'medium', name: 'Egmore' },
}

export const DEMO_ACCOUNTS = [
  { label: 'Priya S. — Velachery (Tamil)', partner_id: 'ZMT001', platform: 'zomato', lang: 'ta' },
  { label: 'Ravi K. — Anna Nagar (Tamil)', partner_id: 'SWG001', platform: 'swiggy', lang: 'ta' },
  { label: 'Mohammed A. — Tambaram (Hindi)', partner_id: 'ZMT002', platform: 'zomato', lang: 'hi' },
]
