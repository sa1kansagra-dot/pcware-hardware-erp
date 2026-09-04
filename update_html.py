with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Title
html = html.replace('<title>TechPulse | Computer Hardware E-Commerce & Service ERP</title>', '<title>PCWARE | Computer Hardware, Custom PC & IT Care ERP</title>')

# 2. Update Top Announcement Bar
old_top_bar = '''  <!-- Top Announcement Bar -->
  <div class="bg-slate-900 text-slate-300 text-xs py-2 px-4 border-b border-slate-800">
    <div class="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
      <div class="flex items-center space-x-4">
        <span class="flex items-center text-emerald-400 font-medium">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
          Store & Hardware Lab Open: 10:00 AM - 8:30 PM
        </span>
        <span class="hidden md:inline text-slate-500">|</span>
        <span class="hidden md:inline">📍 University Road, Ahmedabad, Gujarat</span>
      </div>
      <div class="flex items-center space-x-4 text-slate-400">
        <span>GSTIN: <strong class="text-slate-200">24AABCT1345L1Z8</strong></span>
        <span>📞 Helpline: <strong class="text-slate-200">+91 98250 12345</strong></span>
      </div>
    </div>
  </div>'''

new_top_bar = '''  <!-- Top Announcement Bar -->
  <div class="bg-slate-900 text-slate-300 text-xs py-2 px-4 border-b border-slate-800">
    <div class="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
      <div class="flex items-center space-x-4">
        <span class="flex items-center text-emerald-400 font-medium">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
          Store & Hardware Lab Open: 10:00 AM - 8:30 PM
        </span>
        <span class="hidden md:inline text-slate-500">|</span>
        <span class="hidden md:inline">📍 Suvarnabhumi Complex, Mota Mava, Rajkot</span>
      </div>
      <div class="flex flex-wrap items-center gap-3 text-slate-400 text-[11px]">
        <span>GSTIN: <strong class="text-slate-200 font-mono">24AABCP1234F1Z5</strong></span>
        <span>👔 CEO: <strong class="text-slate-200 font-bold">+91 94261 83934</strong></span>
        <span>🔧 Service: <strong class="text-slate-200 font-bold">+91 80007 80704</strong></span>
        <span>💬 Inquiry: <strong class="text-slate-200 font-bold">+91 70167 37271</strong></span>
      </div>
    </div>
  </div>'''

html = html.replace(old_top_bar, new_top_bar)

# 3. Update Brand Logo & Navigation
old_logo = '''        <!-- Brand Logo -->
        <div class="flex items-center space-x-3 cursor-pointer" onclick="switchView('catalog')">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
          </div>
          <div>
            <div class="font-extrabold text-xl tracking-tight text-slate-900 flex items-center gap-1.5">
              <span>TechPulse</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded bg-brand-100 text-brand-700 border border-brand-200">IT CARE & ERP</span>
            </div>
            <p class="text-[11px] text-slate-500 font-medium" data-i18n="tagline">કમ્પ્યુટર હાર્ડવેર, કસ્ટમ પીસી અને સર્વિસ હબ</p>
          </div>
        </div>'''

new_logo = '''        <!-- Brand Logo -->
        <div class="flex items-center space-x-3 cursor-pointer" onclick="switchView('catalog')">
          <img src="/static/logo.svg" alt="PCWARE" class="h-10 w-auto object-contain">
          <div>
            <div class="font-extrabold text-xl tracking-tight text-slate-900 flex items-center gap-1.5">
              <span>PCWARE</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded bg-orange-100 text-orange-700 border border-orange-200">IT CARE & ERP</span>
            </div>
            <p class="text-[11px] text-slate-500 font-medium" data-i18n="tagline">Computer Hardware Sales, Custom PC Builds & Service Hub</p>
          </div>
        </div>'''

html = html.replace(old_logo, new_logo)

# 4. Update Desktop Navigation Links to default English text
html = html.replace('<span data-i18n="nav_shop">હાર્ડવેર શોપ (Shop)</span>', '<span data-i18n="nav_shop">Hardware Shop</span>')
html = html.replace('<span data-i18n="nav_track">જોબ-શીટ ટ્રેકર (Track Repair)</span>', '<span data-i18n="nav_track">Track Repair</span>')
html = html.replace('<span data-i18n="nav_book">સર્વિસ બુકિંગ (Book Service)</span>', '<span data-i18n="nav_book">Book Service</span>')
html = html.replace('<span data-i18n="nav_erp">ERP પોર્ટલ</span>', '<span data-i18n="nav_erp">ERP Portal</span>')

# 5. Language Switcher: default EN active
old_lang_sw = '''          <!-- Language Toggle Switcher -->
          <div class="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs font-bold">
            <button type="button" id="btn-lang-gu" onclick="setLanguage('gu')" class="px-2 py-1 rounded-lg transition cursor-pointer bg-white text-brand-600 shadow-sm">ગુજરાતી</button>
            <button type="button" id="btn-lang-en" onclick="setLanguage('en')" class="px-2 py-1 rounded-lg transition cursor-pointer text-slate-600 hover:text-slate-900">EN</button>
          </div>'''

new_lang_sw = '''          <!-- Language Toggle Switcher -->
          <div class="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs font-bold">
            <button type="button" id="btn-lang-en" onclick="setLanguage('en')" class="px-2.5 py-1 rounded-lg transition cursor-pointer bg-white text-brand-600 shadow-sm">EN</button>
            <button type="button" id="btn-lang-gu" onclick="setLanguage('gu')" class="px-2.5 py-1 rounded-lg transition cursor-pointer text-slate-600 hover:text-slate-900">ગુજરાતી</button>
          </div>'''

html = html.replace(old_lang_sw, new_lang_sw)

# 6. Hero section default to English
html = html.replace('''          <h1 class="text-3xl sm:text-4xl font-black tracking-tight leading-tight" data-i18n="hero_title">
            કમ્પ્યુટર પાર્ટ્સ, લેપટોપ અને કસ્ટમ પીસી સોલ્યુશન્સ
          </h1>
          <p class="text-slate-300 text-sm sm:text-base" data-i18n="hero_desc">
            Intel 14th Gen, AMD Ryzen 7000, RTX 4000 Series, Gen4 NVMe SSDs અને લેપટોપ રિપેરિંગની સર્વોત્તમ સેવા એક જ સ્થળે.
          </p>
          <div class="pt-2 flex flex-wrap gap-3">
            <button type="button" onclick="switchView('builder')" class="bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-lg shadow-brand-500/30 transition flex items-center gap-2 cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              <span data-i18n="hero_btn_builder">કસ્ટમ PC કન્ફિગર કરો</span>
            </button>
            <button type="button" onclick="switchView('track')" class="bg-white/10 hover:bg-white/20 text-white border border-white/20 font-semibold text-sm px-5 py-2.5 rounded-xl transition flex items-center gap-2 cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <span data-i18n="hero_btn_track">રિપેરિંગ સ્ટેટસ જુઓ</span>
            </button>
          </div>''', '''          <h1 class="text-3xl sm:text-4xl font-black tracking-tight leading-tight" data-i18n="hero_title">
            Computer Parts, Laptops & Custom PC Solutions
          </h1>
          <p class="text-slate-300 text-sm sm:text-base" data-i18n="hero_desc">
            One-stop destination for Intel 14th Gen, AMD Ryzen 7000, RTX 4000 Series, Gen4 NVMe SSDs and expert laptop repair services in Rajkot.
          </p>
          <div class="pt-2 flex flex-wrap gap-3">
            <button type="button" onclick="switchView('builder')" class="bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-lg shadow-orange-500/30 transition flex items-center gap-2 cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              <span data-i18n="hero_btn_builder">Configure Custom PC</span>
            </button>
            <button type="button" onclick="switchView('track')" class="bg-white/10 hover:bg-white/20 text-white border border-white/20 font-semibold text-sm px-5 py-2.5 rounded-xl transition flex items-center gap-2 cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <span data-i18n="hero_btn_track">View Repair Status</span>
            </button>
          </div>''')

# 7. Add rich PCWARE Footer
footer_html = '''
  <!-- PCWARE Comprehensive Footer -->
  <footer class="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800 mt-16 no-print">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-slate-800">
        <!-- Col 1: About PCWARE -->
        <div class="space-y-4">
          <div class="flex items-center space-x-3">
            <img src="/static/logo.svg" alt="PCWARE" class="h-9 w-auto object-contain">
            <span class="text-xl font-extrabold text-white tracking-tight">PCWARE</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Computer Hardware Sales, Custom Gaming & Workstation PC Builds, Component Level Laptop Repairing & Corporate AMC Care in Rajkot, Gujarat.
          </p>
          <div class="text-xs text-slate-400 space-y-1">
            <p><strong>GSTIN:</strong> <span class="font-mono text-slate-200">24AABCP1234F1Z5</span></p>
            <p><strong>Hours:</strong> Mon - Sat: 10:00 AM - 8:30 PM</p>
          </div>
        </div>

        <!-- Col 2: Store & Workshop Address -->
        <div class="space-y-3">
          <h4 class="text-sm font-bold text-white uppercase tracking-wider">Store & Service Hub</h4>
          <p class="text-xs text-slate-400 leading-relaxed">
            Shop No. SF, 47, 48, 49, Suvarnabhumi Complex,<br>
            opp. Speedwell Party Plot, Ambika Twp, Mota Mava,<br>
            Rajkot, Gujarat - 360005
          </p>
          <p class="text-xs text-brand-400 font-semibold">
            📍 Landmark: Opp. Speedwell Party Plot
          </p>
        </div>

        <!-- Col 3: Direct Contact Numbers -->
        <div class="space-y-3">
          <h4 class="text-sm font-bold text-white uppercase tracking-wider">Direct Contacts</h4>
          <ul class="text-xs space-y-2 text-slate-400">
            <li class="flex items-center gap-2">
              <span class="text-slate-500 font-bold w-16">CEO:</span>
              <a href="tel:9426183934" class="text-slate-200 hover:text-white font-bold">+91 94261 83934</a>
            </li>
            <li class="flex items-center gap-2">
              <span class="text-slate-500 font-bold w-16">Service:</span>
              <a href="tel:8000780704" class="text-emerald-400 hover:text-emerald-300 font-bold">+91 80007 80704</a>
            </li>
            <li class="flex items-center gap-2">
              <span class="text-slate-500 font-bold w-16">Inquiry:</span>
              <a href="tel:7016737271" class="text-orange-400 hover:text-orange-300 font-bold">+91 70167 37271</a>
            </li>
            <li class="flex items-center gap-2 pt-1">
              <span class="text-slate-500 font-bold w-16">Email:</span>
              <a href="mailto:info@pcware.in" class="text-slate-300 hover:text-white">info@pcware.in</a>
            </li>
          </ul>
        </div>

        <!-- Col 4: Quick Navigation -->
        <div class="space-y-3">
          <h4 class="text-sm font-bold text-white uppercase tracking-wider">Quick Links</h4>
          <ul class="text-xs space-y-2 text-slate-400">
            <li><a href="javascript:switchView('catalog')" class="hover:text-white transition">🛍️ Hardware Catalog</a></li>
            <li><a href="javascript:switchView('builder')" class="hover:text-white transition">⚙️ Custom PC Configurator</a></li>
            <li><a href="javascript:switchView('track')" class="hover:text-white transition">🔍 Track Job Sheet / Repair</a></li>
            <li><a href="javascript:switchView('book')" class="hover:text-white transition">📅 Book Service Token</a></li>
            <li><a href="javascript:switchView('admin')" class="hover:text-white transition">📊 ERP & Billing Portal</a></li>
          </ul>
        </div>
      </div>

      <div class="pt-6 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-3">
        <p>© 2026 PCWARE. All rights reserved. Registered Computer Hardware & IT Services Enterprise.</p>
        <p>100% Genuine Components • Serial Warranty Tracking</p>
      </div>
    </div>
  </footer>
'''

if '</main>' in html and '<!-- PCWARE Comprehensive Footer -->' not in html:
    html = html.replace('</main>', '</main>\n' + footer_html)

# 8. City default in New Party modal
html = html.replace('value="અમદાવાદ"', 'value="રાજકોટ"')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Updated static/index.html successfully!')
