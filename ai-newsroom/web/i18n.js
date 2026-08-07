/* i18n.js — વેબસાઈટની ભાષા (English / ગુજરાતી)
 *
 * The whole dashboard UI can run in English. News content, headlines,
 * bodies and posters always stay Gujarati — only known UI phrases are
 * swapped, so nothing you write ever gets translated by accident.
 *
 * Default: English. Toggle in the sidebar switches back to Gujarati.
 */
(function () {
  "use strict";

  var LANG = localStorage.getItem("ui_lang") || "en";

  /* ── ચોક્કસ શબ્દકોશ (exact phrase → English) ───────────────── */
  var D = {
    // --- નેવિગેશન / ચોકઠાં ---
    "ડેશબોર્ડ": "Dashboard",
    "અપ્રુવલ": "Approvals",
    "બધા ન્યુઝ": "All News",
    "રિપોર્ટ": "Reports",
    "સેટિંગ": "Settings",
    "વર્ઝન ...": "Version ...",
    "🌙 થીમ બદલો": "🌙 Switch Theme",
    "🌞 થીમ બદલો": "🌞 Switch Theme",
    "ન્યુઝરૂમ ડેશબોર્ડ": "Newsroom Dashboard",
    "● લાઈવ": "● LIVE",
    "🚀 દિવસ શરૂ કરો": "🚀 Start the Day",

    // --- KPI ---
    "ભેગા કર્યા": "Collected",
    "પસંદ કર્યા": "Selected",
    "લખાયા": "Written",
    "પોસ્ટર": "Posters",
    "મંજૂર": "Approved",
    "ન્યુઝ": "News",
    "FB પોસ્ટ": "FB Posts",
    "ભૂલ": "Errors",

    // --- એજન્ટ ---
    "નિષ્ક્રિય": "Idle",
    "સ્કાઉટ": "Scout",
    "લેખક": "Writer",
    "શુદ્ધિ": "Proofreader",
    "ડિઝાઈનર": "Designer",
    "ફોટો": "Photo",
    "પબ્લિશર": "Publisher",
    "જવાબ": "Inbox",
    "એનાલિસ્ટ": "Analyst",
    "વિચારે છે...": "thinking...",
    "કામ ચાલુ": "Working",
    "અપ્રુવલ રાહ": "Awaiting approval",
    "પૂર્ણ ✓": "Done ✓",
    "ભૂલ!": "Error!",
    "📋 લાઈવ લોગ": "📋 Live Log",

    // --- પ્રેસ નોટ ---
    "📝 પ્રેસ નોટ": "📝 Press Note",
    "પ્રેસ નોટ પેસ્ટ કરો — AI ન્યુઝ લખી, પોસ્ટર બનાવી અપ્રુવલમાં મૂકશે.":
      "Paste a press note — the AI writes the news, builds the poster " +
      "and sends it for approval.",
    "✍️ રિપોર્ટરનું નામ (પોસ્ટરમાં આવશે)":
      "✍️ Reporter name (shown on the poster)",
    "📷 ફોટા જોડો — 3 સુધી (પોસ્ટરમાં કોલાજ બનશે)":
      "📷 Attach photos — up to 3 (collage on the poster)",
    "📄 PDF પ્રેસ નોટ (આખી PDF માંથી બધા ન્યુઝ)":
      "📄 PDF press note (every news item in the PDF)",
    "📍 જિલ્લો (ડિફોલ્ટ)": "📍 District (default)",
    "ન્યુઝ બનાવો →": "Create News →",
    "પ્રેસ નોટનું લખાણ અહીં પેસ્ટ કરો...": "Paste the press note text here...",
    "પ્રેસ નોટનું લખાણ લખો": "Please enter the press note text",

    // --- અપ્રુવલ / ન્યુઝ ---
    "અપ્રુવલની રાહમાં": "Waiting for approval",
    "પોસ્ટર જુઓ → મંજૂર કરો કે રદ કરો": "Review the poster → approve or reject",
    "આજ સુધીના બધા ન્યુઝ — સ્ટેટસ પ્રમાણે": "All news so far — by status",
    "બધા": "All",
    "🟠 રાહમાં": "🟠 Pending",
    "📤 પબ્લિશ": "📤 Published",
    "✅ મંજૂર": "✅ Approved",
    "❌ રદ": "❌ Rejected",
    "🔍 શબ્દ/વિષય શોધો...": "🔍 Search word or topic...",
    "કોઈ ન્યુઝ અપ્રુવલની રાહમાં નથી 🎉": "Nothing waiting for approval 🎉",
    "કોઈ ન્યુઝ નથી": "No news yet",
    "✅ મંજૂર + પબ્લિશ": "✅ Approve + Publish",
    "રદ કરો": "Reject",
    "પોસ્ટ": "Post",
    "પોર્ટ્રેટ": "Portrait",
    "સ્ટોરી": "Story",
    "હેડલાઈન": "Headline",
    "લખાણ": "Body text",
    "💾 સેવ + પોસ્ટર ફરી બનાવો": "💾 Save + Rebuild poster",
    "✨ સારાંશ": "✨ Summary",
    "🎬 વિડિયો (Reels)": "🎬 Video (Reels)",
    "⏰ શેડ્યૂલ પબ્લિશ:": "⏰ Schedule publish:",
    "સેટ કરો": "Set",
    "લખાયો": "Written",
    "ડ્રાફ્ટ": "Draft",

    // --- કેટેગરી ---
    "સમાચાર": "News",
    "બ્રેકિંગ": "Breaking",
    "જન્મદિવસ": "Birthday",
    "શ્રદ્ધાંજલિ": "Tribute",

    // --- રિપોર્ટ ---
    "મહિનાનો સાર": "This month at a glance",
    "📱 WhatsApp રિપોર્ટ": "📱 WhatsApp report",
    "💰 એકાઉન્ટન્ટ — આ મહિનાનો ખર્ચ": "💰 Accountant — spend this month",
    "📈 રોજના ન્યુઝ": "📈 News per day",
    "📅 તારીખવાર": "📅 Day by day",
    "🤖 એજન્ટ પરફોર્મન્સ": "🤖 Agent performance",
    "આ મહિને ડેટા નથી": "No data this month",
    "આ મહિને ખર્ચ નથી": "No spend this month",
    "તારીખ": "Date",
    "ભેગા": "Collected",
    "રદ": "Rejected",
    "એજન્ટ": "Agent",
    "રન": "Runs",
    "સરેરાશ સમય": "Avg time",
    "પ્રકાર": "Type",
    "સર્વિસ": "Service",
    "સંખ્યા": "Count",
    "ખર્ચ ₹": "Cost ₹",
    "🖼️ તસવીર": "🖼️ Image",
    "✍️ લખાણ": "✍️ Text",
    "રિપોર્ટ WhatsApp પર મોકલ્યો ✓": "Report sent on WhatsApp ✓",

    // --- સેટિંગ: ચેનલ ---
    "એક વાર ગોઠવો, રોજ આરામ": "Set it up once, relax every day",
    "📺 ચેનલ": "📺 Channel",
    "ચેનલનું નામ": "Channel name",
    "ટેગલાઈન (પોસ્ટરમાં ઉપર આવે)": "Tagline (shown at the top of the poster)",
    "તંત્રીનું નામ": "Editor name",
    "સંપર્ક નંબર (પોસ્ટરમાં \"ઘટના મોકલો\" સ્ટ્રીપ)":
      "Contact number (the \"send us news\" strip on the poster)",
    "સ્થળ": "Location",
    "રોજના ન્યુઝ": "News per day",
    "ઓટો રન સમય": "Auto-run time",
    "રોજ ઓટો ચલાવો": "Run automatically every day",

    // --- સેટિંગ: બ્રાન્ડિંગ ---
    "🎨 બ્રાન્ડિંગ / ડિઝાઈન": "🎨 Branding / Design",
    "🖼️ લોગો અપલોડ (PD બોક્સને બદલે)": "🖼️ Upload logo (replaces the PD box)",
    "લોગો સેવ કરો": "Save logo",
    "લોગો કાઢો": "Remove logo",
    "પોસ્ટર ફોન્ટ (હેડલાઈન)": "Poster font (headline)",
    "Anek Gujarati (ડિફોલ્ટ)": "Anek Gujarati (default)",
    "Baloo Bhai 2 (જાડું, હેડલાઈન)": "Baloo Bhai 2 (bold, headline)",
    "Farsan (સ્ટાઈલિશ)": "Farsan (stylish)",
    "વેબસાઈટ URL": "Website URL",
    "મુખ્ય રંગ": "Primary colour",
    "લાલ": "Red",
    "પોસ્ટર પર QR કોડ બતાવો": "Show QR code on poster",
    "ફોટા પર ચેનલ વોટરમાર્ક": "Channel watermark on photos",
    "QR માં શું (ખાલી = વેબસાઈટ)": "QR contents (empty = website)",
    "હેશટેગ (સોશિયલ કેપ્શન માટે)": "Hashtags (for social captions)",
    "❌ કચરો શબ્દો (આ શબ્દવાળા ન્યુઝ કાઢી નાખો)":
      "❌ Junk words (drop any news containing these)",

    // --- સેટિંગ: લેખન AI ---
    "✍️ ન્યુઝ લેખન AI (રિરાઈટ)": "✍️ News writing AI (rewrite)",
    "દરેક ન્યુઝ મૌલિક રીતે રિરાઈટ થાય — કોપીરાઈટ ટાળવા. Ollama ન હોય તો Gemini વાપરો (તમારી key).":
      "Every story is rewritten in original words to avoid copyright " +
      "trouble. No Ollama? Use Gemini with your own key.",
    "સર્વિસ પસંદ કરો": "Choose a service",
    "☁️ AIAuto — તમારું પ્લેટફોર્મ": "☁️ AIAuto — your own platform",
    "🖥️ Ollama — લોકલ (તમારા GPU પર)": "🖥️ Ollama — local (on your GPU)",
    "🔷 Google Gemini — તમારી key": "🔷 Google Gemini — your key",
    "🟢 OpenAI — તમારી key": "🟢 OpenAI — your key",
    "ઈમેજ વાળું એ જ AIAuto પ્લેટફોર્મ વાપરે — URL/Key ઉપર \"AI તસવીર\" વિભાગમાં ભરેલા છે. અહીં કંઈ ભરવાનું નથી.":
      "Uses the same AIAuto platform as images — the URL and key are " +
      "already set in the \"AI Images\" section above. Nothing to fill in here.",
    "મોડેલ (ખાલી = ડિફોલ્ટ)": "Model (empty = default)",
    "Ollama તમારા કોમ્પ્યુટર પર ચાલુ હોવું જોઈએ.":
      "Ollama must be running on your computer.",
    "વિચાર મોડેલ": "Thinking model",
    "લેખન મોડેલ": "Writing model",
    "🧪 લેખન ટેસ્ટ કરો": "🧪 Test writing",
    "Instagram માટે: IG Business એકાઉન્ટ FB Page સાથે જોડાયેલું + ટોકનમાં instagram_content_publish permission.":
      "For Instagram: an IG Business account linked to the FB Page, plus " +
      "the instagram_content_publish permission on the token.",

    // --- સેટિંગ: AI તસવીર ---
    "🖼️ AI તસવીર": "🖼️ AI Images",
    "સાચો ફોટો ન હોય ત્યારે હેડલાઈન પરથી AI તસવીર આપોઆપ બને. પ્રોમ્પ્ટ સિસ્ટમ પોતે બનાવે — તમારે કંઈ લખવાનું નહીં.":
      "When there is no real photo, an AI image is built from the " +
      "headline automatically. The system writes the prompt — you don't " +
      "have to write anything.",
    "AI તસવીર ચાલુ કરો": "Enable AI images",
    "🖥️ લોકલ SD (તમારા GPU પર) — ₹0": "🖥️ Local SD (on your GPU) — ₹0",
    "🆓 Pollinations — મફત (ઓનલાઈન)": "🆓 Pollinations — free (online)",
    "તમારું પોતાનું પ્લેટફોર્મ — કોઈ third-party key નહીં.":
      "Your own platform — no third-party key needed.",
    "સાથે ચાલુ હોવું જોઈએ.": "must be running.",
    "લોકલ SD URL": "Local SD URL",
    "મફત, કોઈ key જોઈએ નહીં — ફક્ત ઈન્ટરનેટ. ટેસ્ટિંગ માટે સારું.":
      "Free, no key needed — just internet. Good for testing.",
    "ક્વોલિટી": "Quality",
    "low — ~₹1/તસવીર": "low — ~₹1/image",
    "medium — ~₹3.5/તસવીર": "medium — ~₹3.5/image",
    "high — ~₹14/તસવીર": "high — ~₹14/image",
    "🤖 એડવાન્સ — ઓટો પ્રોમ્પ્ટ નિયમો (સામાન્ય રીતે બદલવાની જરૂર નથી)":
      "🤖 Advanced — auto prompt rules (you normally don't need these)",
    "ક્વોલિટી ટૅગ (દરેક પ્રોમ્પ્ટ પાછળ આપોઆપ)":
      "Quality tags (appended to every prompt automatically)",
    "નેગેટિવ પ્રોમ્પ્ટ (શું ન જોઈએ)": "Negative prompt (what to avoid)",
    "વધારાની સ્ટાઈલ સૂચના (વૈકલ્પિક — ખાલી રાખવું સારું)":
      "Extra style instruction (optional — best left empty)",
    "⚠️ અહીં કચરો લખાણ (દા.ત. \"test\") હોય તો ફોટો ખોટો આવે — આ ખાના પ્રોમ્પ્ટમાં જોડાય છે.":
      "⚠️ Junk text here (e.g. \"test\") ruins the image — these fields " +
      "are added to the prompt.",
    "↩️ ડિફોલ્ટ પર રીસેટ કરો": "↩️ Reset to defaults",
    "🧪 ટેસ્ટ તસવીર બનાવો": "🧪 Generate a test image",
    "🔎 કનેક્શન તપાસો": "🔎 Check connection",
    "લોકલ SD": "Local SD",
    "aistudio.google.com/apikey પરથી key લો. ~₹3/તસવીર.":
      "Get a key from aistudio.google.com/apikey. ~₹3/image.",
    "platform.openai.com → API keys. બિલિંગ અલગ છે.":
      "platform.openai.com → API keys. Billing is separate.",
    "જે પ્રોમ્પ્ટ મોકલાયો:": "Prompt that was sent:",

    // --- સેટિંગ: Telegram / WhatsApp ---
    "📢 Telegram ચેનલ (મફત)": "📢 Telegram channel (free)",
    "@BotFather થી બોટ બનાવો → ચેનલમાં Admin બનાવો. પોસ્ટર આપોઆપ ચેનલ પર જશે — verification વગર, ₹0.":
      "Create a bot with @BotFather → make it an Admin of your channel. " +
      "Posters go out automatically — no verification, ₹0.",
    "🧪 ટેસ્ટ મેસેજ": "🧪 Test message",
    "📱 WhatsApp જાણ (તમારી API)": "📱 WhatsApp alerts (your API)",
    "તમારો WhatsApp નંબર (91 સાથે)": "Your WhatsApp number (with 91)",
    "બ્રોડકાસ્ટ નંબર (અલ્પવિરામથી અલગ, 91 સાથે)":
      "Broadcast numbers (comma separated, with 91)",
    "⚡ ન્યુઝ બનતાં જ મોકલો (અપ્રુવલ પહેલાં)":
      "⚡ Send as soon as the news is built (before approval)",
    "ચાલુ કરો એટલે પોસ્ટર બની જાય કે તરત નીચેના કોમન નંબર કે ગ્રુપ પર જતું રહેશે — વેબસાઈટ પર અપ્રુવલ પછીથી આપી શકાય.":
      "Turn this on and the poster goes straight to the common number or " +
      "group below the moment it is built — you can approve it on the " +
      "website afterwards.",
    "કોમન નંબર કે ગ્રુપ ID": "Common number or group ID",
    "919978123146  કે  120363...@g.us": "919978123146  or  120363...@g.us",
    "નંબર 91 સાથે લખો. ગ્રુપમાં મોકલવું હોય તો ગ્રુપ ID આખું @g.us સાથે નાખો. ખાલી રાખશો તો ઉપરનો તમારો WhatsApp નંબર વપરાશે.":
      "Write the number with 91. For a group, paste the full group ID " +
      "including @g.us. Leave it empty to use your WhatsApp number above.",
    "🧪 કોમન નંબર/ગ્રુપ ટેસ્ટ કરો": "🧪 Test the common number/group",
    "ટેસ્ટ મોકલાયો ✓": "Test sent ✓",
    "⚡ WhatsApp પર ગયું": "⚡ Sent on WhatsApp",
    "WhatsApp મોકલો": "Send on WhatsApp",
    "કોમન નંબર કે ગ્રુપ ID ભરીને સેવ કરો":
      "Enter the common number or group ID and save",
    "રાત્રે 9 વાગ્યે રોજનો રિપોર્ટ મોકલો": "Send the daily report at 9 pm",
    "ભૂલ પડે તો WhatsApp એલર્ટ": "WhatsApp alert when something fails",
    "Public URL (વૈકલ્પિક — તમારી hosting)":
      "Public URL (optional — your hosting)",
    "🧪 ટેસ્ટ મેસેજ મોકલો": "🧪 Send a test message",

    // --- સેટિંગ: યુઝર / અપડેટ ---
    "👥 યુઝર / લોગિન": "👥 Users / Login",
    "લોગિન ફરજિયાત કરો (એડમિન + રિપોર્ટર)":
      "Require login (admin + reporter)",
    "ડિફોલ્ટ એડમિન:": "Default admin:",
    "— ચાલુ કર્યા પછી તરત પાસવર્ડ બદલો. રિપોર્ટર ન્યુઝ બનાવે, ફક્ત એડમિન મંજૂર/પબ્લિશ કરે.":
      "— change the password as soon as you turn this on. Reporters " +
      "create news; only admins approve and publish.",
    "🔄 GitHub અપડેટ": "🔄 GitHub update",
    "ચેક કરો": "Check",
    "💾 બેકઅપ": "💾 Backup",
    "🔄 સર્વર રીસ્ટાર્ટ": "🔄 Restart server",
    "સેવ કરો": "Save",
    "સેટિંગ સેવ થઈ ગયું ✓": "Settings saved ✓",

    // --- મોડલ / લોગિન ---
    "🚀 આજનો દિવસ શરૂ કરીએ?": "🚀 Start today's run?",
    "આજે કેટલા ન્યુઝ બનાવવા?": "How many news items today?",
    "કેટલી AI તસવીર બનાવવી? (0 = એક પણ નહીં)":
      "How many AI images? (0 = none)",
    "🚀 શરૂ કરો": "🚀 Start",
    "લોગિન કરો": "Sign in",
    "લોગિન": "Login",
    "યુઝરનેમ": "Username",
    "પાસવર્ડ": "Password",
    "લોગિન નિષ્ફળ": "Login failed",
    "એડમિન લોગિન જોઈએ": "Admin login required",
    "ખોટું નામ કે પાસવર્ડ": "Wrong username or password",

    // --- પ્લેસહોલ્ડર ---
    "દા.ત. શ્રી અક્ષયભાઈ કાનાણી": "e.g. Shri Akshaybhai Kanani",
    "દા.ત. 9978123146": "e.g. 9978123146",
    "દા.ત. રાશિફળ, જ્યોતિષ, જાહેરાત":
      "e.g. horoscope, astrology, advertisement",
    "દા.ત. drone view, golden hour light":
      "e.g. drone view, golden hour light",
    "દા.ત. 919978123146": "e.g. 919978123146",
    "દા.ત. https://news.akdwk.in": "e.g. https://news.akdwk.in",

    // --- ટોસ્ટ / સ્ટેટસ ---
    "Ollama ચાલુ": "Ollama online",
    "Ollama બંધ — ડેમો મોડ": "Ollama offline — demo mode",
    "⚠️ સેટિંગમાં AI તસવીર બંધ છે — પહેલા ચાલુ કરો":
      "⚠️ AI images are off in Settings — turn them on first",
    "AI તસવીર નહીં બને — ખર્ચ ₹0": "No AI images — cost ₹0",
    "મંજૂર ✓ (ટોકન વગર — સિમ્યુલેશન પબ્લિશ)":
      "Approved ✓ (no token — simulated publish)",
    "મંજૂર + પબ્લિશ થઈ ગયું ✓": "Approved and published ✓",
    "ન્યુઝ રદ કર્યો": "News rejected",
    "બની રહ્યું છે...": "Building...",
    "પોસ્ટર ફરી બન્યું ✓": "Poster rebuilt ✓",
    "પહેલા સમય પસંદ કરો": "Pick a time first",
    "શેડ્યૂલ થઈ ગયું — સમય થાય એટલે આપોઆપ પબ્લિશ ⏰":
      "Scheduled — it will publish automatically ⏰",
    "વિડિયો બની રહ્યો છે... (~10-20 સે)": "Making the video... (~10-20 s)",
    "વોઈસ-ઓવર (અવાજ) પણ ઉમેરવો?": "Add a voice-over as well?",
    "(edge-tts ઈન્સ્ટોલ હોવું જોઈએ)": "(edge-tts must be installed)",
    "વિડિયો ભૂલ": "Video error",
    "લખાવી રહ્યો છું... (પહેલા સેવ કરો)": "Writing... (save first)",
    "લેખન ટેસ્ટ પાસ ✓": "Writing test passed ✓",
    "ચેક થઈ રહ્યું છે...": "Checking...",
    "અપડેટ શરૂ કરવું? બેકઅપ આપોઆપ લેવાશે.":
      "Start the update? A backup is taken automatically.",
    "અપડેટ ચાલી રહ્યું છે...": "Update in progress...",
    "તસવીર બની રહી છે... (~30-60 સેકન્ડ, પહેલા સેવ કરો ભૂલતા નહીં)":
      "Generating the image... (~30-60 s — remember to save first)",
    "AI તસવીર બની ✓": "AI image created ✓",
    "AI તસવીર ભૂલ": "AI image error",
    "તપાસી રહ્યો છું...": "Checking...",
    "બધું બરાબર — API ચાલે છે.": "All good — the API is working.",
    "હવે ટેસ્ટ તસવીર બનાવો.": "Now generate a test image.",
    "જ્યાં ❌ છે ત્યાં ભૂલ છે": "The ❌ step is where the problem is",
    "— એ સ્ટેપ ઠીક કરો. (સ્ટેપ 2 ❌ = AIAuto સર્વર/કોમ્પ્યુટર બંધ, સ્ટેપ 3 ❌ = API Key ખોટી, સ્ટેપ 4 ❌ = API બાજુની ભૂલ)":
      "— fix that step. (Step 2 ❌ = AIAuto server/computer is off, " +
      "Step 3 ❌ = wrong API key, Step 4 ❌ = problem on the API side)",
    "કનેક્શન બરાબર ✓": "Connection OK ✓",
    "કનેક્શનમાં ભૂલ મળી": "Connection problem found",
    "ડિફોલ્ટ પર આવી ગયું — હવે 'સેવ કરો' દબાવો":
      "Reset to defaults — now press Save",
    "પહેલા લોગો ફાઈલ પસંદ કરો": "Choose a logo file first",
    "લોગો સેવ થયો ✓ — હવે પોસ્ટરમાં આવશે":
      "Logo saved ✓ — it will appear on posters",
    "લોગો સેવ થયો ✓": "Logo saved ✓",
    "લોગો કઢાયો — ફરી PD બોક્સ આવશે":
      "Logo removed — the PD box comes back",
    "લોગો કઢાયો": "Logo removed",
    "મોકલી રહ્યો છું... (પહેલા સેવ કરો)": "Sending... (save first)",
    "મોકલી રહ્યો છું... (પહેલા સેવ કરો ભૂલતા નહીં)":
      "Sending... (remember to save first)",
    "✅ Telegram ચેનલ ચેક કરો!": "✅ Check your Telegram channel!",
    "Telegram ટેસ્ટ ✓": "Telegram test ✓",
    "Telegram ભૂલ": "Telegram error",
    "✅ મોકલાઈ ગયું — તમારો WhatsApp ચેક કરો!":
      "✅ Sent — check your WhatsApp!",
    "WhatsApp ટેસ્ટ મોકલાયો ✓": "WhatsApp test sent ✓",
    "WhatsApp ભૂલ": "WhatsApp error",
    "બેકઅપ લેવાઈ ગયો ✓": "Backup taken ✓",
    "સર્વર રીસ્ટાર્ટ કરવું? 5-10 સેકન્ડમાં ફરી ચાલુ થશે.":
      "Restart the server? It comes back in 5-10 seconds.",
    "સર્વર રીસ્ટાર્ટ થઈ રહ્યું છે... પેજ આપોઆપ ફરી લોડ થશે":
      "Restarting the server... this page will reload by itself",
    "સર્વર રીસ્ટાર્ટ થઈ રહ્યું છે...": "Restarting the server...",

    // --- સર્વર બાજુના મેસેજ (progress / errors) ---
    "કામ પહેલેથી ચાલુ છે": "A run is already in progress",
    "દિવસ શરૂ — કામ વહેંચી રહ્યો છું...": "Day started — assigning work...",
    "દિવસ શરૂ થયો": "Day started",
    "દિવસ શરૂ થયો 🚀": "Day started 🚀",
    "શરૂ": "Start",
    "RSS ફીડ વાંચી રહ્યો છું...": "Reading RSS feeds...",
    "ન્યુઝ શોધો": "Find news",
    "પસંદગી": "Selection",
    "તપાસો": "Proofread",
    "AI તસવીર": "AI image",
    "આંકડા": "Stats",
    "પૂર્ણ": "Done",
    "આજના આંકડા ગણી રહ્યો છું...": "Counting today's numbers...",
    "પ્રેસ નોટ પર કામ શરૂ 🚀": "Working on the press note 🚀",
    "પ્રેસ નોટનું લખાણ ખાલી છે": "The press note is empty",
    "PDF ના પાનાં જોઈ રહ્યો છું (Vision AI)...":
      "Reading the PDF pages (Vision AI)...",
    "PDF ના પાનાં જોઈ ન્યુઝ કાઢી રહ્યો છું 🚀 (Vision AI)":
      "Reading the PDF pages and extracting news 🚀 (Vision AI)",
    "ન્યુઝ મળ્યો નહીં": "News not found",
    "પહેલા પોસ્ટર બનાવો": "Create the poster first",
    "PDF માટે PyMuPDF જોઈએ — pip install PyMuPDF":
      "PDFs need PyMuPDF — run: pip install PyMuPDF",
    "ઈમેજવાળી PDF વાંચવા Gemini/OpenAI key જોઈએ — સેટિંગ → ન્યુઝ લેખન AI માં Gemini સેટ કરો":
      "Reading an image-based PDF needs a Gemini/OpenAI key — set up " +
      "Gemini under Settings → News writing AI",
    "PDF માંથી ન્યુઝ ન મળ્યા — Gemini key/મોડેલ ચેક કરો (સેટિંગ → ન્યુઝ લેખન AI)":
      "No news found in the PDF — check your Gemini key/model " +
      "(Settings → News writing AI)",
    "WhatsApp API ભરેલું નથી": "WhatsApp API is not configured",
    "સેટિંગમાં WhatsApp API ભરેલું નથી":
      "WhatsApp API is not configured in Settings",
    "પહેલા WhatsApp API સેટિંગ ભરીને સેવ કરો":
      "Fill in the WhatsApp API settings and save first",
    "AI એ ખાલી જવાબ આપ્યો": "The AI returned an empty answer",
    "પહેલા AI તસવીર ચાલુ કરી OpenAI API Key ભરી સેવ કરો":
      "Turn on AI images, enter the OpenAI API key and save first",
    "Telegram ટોકન + chat ભરો": "Enter the Telegram token and chat",
    "Telegram સેટ નથી": "Telegram is not configured",
    "Instagram સેટ નથી": "Instagram is not configured",
    "ફક્ત PNG/JPG લોગો": "Logo must be PNG or JPG",
    "સેટિંગમાં GitHub repo સેટ કરો": "Set the GitHub repo in Settings",
    "પહેલેથી લેટેસ્ટ વર્ઝન છે ✅": "Already on the latest version ✅",
    "(પહેલી વાર)": "(first time)",
    "ટેમ્પ્લેટ ગુમ છે": "Template is missing",
    "💾 બેકઅપ લેવાઈ રહ્યો છે...": "💾 Taking a backup...",
    "⬇️ ડાઉનલોડ થઈ રહ્યું છે...": "⬇️ Downloading...",
    "📦 એક્સટ્રેક્ટ...": "📦 Extracting...",
    "📋 ફાઈલો કોપી (સુરક્ષિત ફોલ્ડર છોડીને)...":
      "📋 Copying files (skipping protected folders)...",
    "🗄️ DB માઈગ્રેશન...": "🗄️ Database migration...",
    "✅ હેલ્થ ચેક...": "✅ Health check...",
    "વર્ઝન નોંધાઈ રહ્યું છે...": "Recording the version...",
    "ffmpeg મળ્યું નથી — ffmpeg.org પરથી ઈન્સ્ટોલ કરો":
      "ffmpeg not found — install it from ffmpeg.org",
    "AIAuto એ job id ન આપ્યો": "AIAuto did not return a job id",
    "AIAuto: પૂરું થયું પણ ઈમેજ નથી":
      "AIAuto: finished, but there is no image",
    "લોકલ SD એ ઈમેજ ન આપી": "Local SD returned no image",
    "1. સેટિંગ": "1. Settings",
    "2. સર્વર સુધી પહોંચ": "2. Reaching the server",
    "3. API Key": "3. API key",
    "4. ઈમેજ સબમિટ": "4. Submitting an image",
    "બરાબર ✓": "OK ✓",
    "કનેક્ટ ન થયું — સેટિંગ ચેક કરો.":
      "Could not connect — check your settings."
  };

  /* ── નિયમો (નંબર/નામ વાળા મેસેજ) ───────────────────────────── */
  var R = [
    [/^વર્ઝન: (.+)$/, "Version: $1"],
    [/^ભરેલી ✓$/, "filled ✓"],
    [/^\(ખાલી\)$/, "(empty)"],
    [/^(\d+) નવા ન્યુઝ મળ્યા$/, "Found $1 new stories"],
    [/^(\d+) માંથી (\d+) પસંદ કરું છું\.\.\.$/, "Picking $2 out of $1..."],
    [/^(\d+) ન્યુઝ પસંદ થયા$/, "$1 stories selected"],
    [/^લેખકને (\d+) ન્યુઝ સોંપ્યા$/, "Handed $1 stories to the writer"],
    [/^ન્યુઝ (\d+)\/(\d+) — રિરાઈટ થઈ રહ્યો છે\.\.\.$/,
      "News $1/$2 — rewriting..."],
    [/^ન્યુઝ #(\d+) (.*)$/, "News #$1 $2"],
    [/^(\d+) ન્યુઝ તૈયાર — અપ્રુવલ બાકી$/,
      "$1 stories ready — awaiting approval"],
    [/^દિવસ પૂરો — (\d+) ન્યુઝ અપ્રુવલ માટે તૈયાર ✅$/,
      "Day complete — $1 stories ready for approval ✅"],
    [/^પાનું (\d+)\/(\d+) વાંચી રહ્યો છું\.\.\.$/, "Reading page $1/$2..."],
    [/^(\d+) ન્યુઝ મળ્યા — બનાવી રહ્યો છું$/, "Found $1 stories — building"],
    [/^PDF ન્યુઝ (\d+)\/(\d+) બન્યો$/, "PDF news $1/$2 done"],
    [/^PDF માંથી (\d+) ન્યુઝ તૈયાર$/, "$1 stories ready from the PDF"],
    [/^PDF ભૂલ: (.*)$/, "PDF error: $1"],
    [/^PDF ભૂલ — (.*)$/, "PDF error — $1"],
    [/^✅ લેટેસ્ટ વર્ઝન છે \((.+)\)$/, "✅ You are on the latest version ($1)"],
    [/^બેકઅપ: (.*)$/, "Backup: $1"],
    [/^ન્યુઝ #(\d+) WhatsApp પર મોકલી રહ્યો છું\.\.\.$/,
      "Sending news #$1 on WhatsApp..."],
    [/^✅ મોકલાઈ ગયું — (.+) \(ગ્રુપ\) ચેક કરો!$/, "✅ Sent — check $1 (group)!"],
    [/^✅ મોકલાઈ ગયું — (.+) \(નંબર\) ચેક કરો!$/, "✅ Sent — check $1 (number)!"],
    [/^✅ બની ગઈ! \((.*)\)$/, "✅ Created! ($1)"],
    [/^💰 આ મહિને AI તસવીર ખર્ચ \((.+)\): ≈ ₹(.+)$/,
      "💰 AI image spend this month ($1): ≈ ₹$2"],
    [/^કુલ ખર્ચ: ₹(.+)$/, "Total spend: ₹$1"],
    [/^(\d+) AI તસવીર \(મફત\) — ખર્ચ ₹0$/, "$1 AI images (free) — cost ₹0"],
    [/^અંદાજિત ખર્ચ: (\d+) તસવીર × ₹(.+) ≈ ₹(.+)$/,
      "Estimated cost: $1 images × ₹$2 ≈ ₹$3"],
    [/^(\d+) AI તસવીર \(AIAuto — ₹0\)\. ⏱️ એક પછી એક બને, દરેકને 1-4 મિનિટ — અંદાજે (\d+)-(\d+) મિનિટ લાગશે\.$/,
      "$1 AI images (AIAuto — ₹0). ⏱️ They run one at a time, 1-4 min " +
      "each — roughly $2-$3 minutes in total."],
    [/^🧪 (.+) થી ટેસ્ટ તસવીર બનાવો$/, "🧪 Generate a test image with $1"],
    [/^🧪 (.+) થી લેખન ટેસ્ટ કરો$/, "🧪 Test writing with $1"],
    [/^(.+) ચાલે છે:$/, "$1 is working:"],
    [/^🎉 નવું અપડેટ છે!$/, "🎉 An update is available!"],
    [/^હાલનું: (.+) → નવું: (.+)$/, "Current: $1 → New: $2"],
    [/^🎉 (.+): (.+) — પોસ્ટર બનાવવાનું યાદ રાખો!$/,
      "🎉 $1: $2 — remember to make a poster!"],
    [/^📈 ટ્રેન્ડિંગ:$/, "📈 Trending:"],
    [/^ટ્રેન્ડિંગ:$/, "Trending:"],
    [/^(.+) ઉપલબ્ધ નથી — key\/URL ચેક કરી સેવ કરો$/,
      "$1 is not available — check the key/URL and save"],
    [/^(\d+(?:\.\d+)?) સે$/, "$1 s"],
    [/^(.+) સુધી પહોંચાતું નથી (.*)$/, "cannot reach $1 $2"],
    [/^(.+) જવાબ આપે છે ✓$/, "$1 responded ✓"],
    [/^\/me માં ભૂલ: (.*)$/, "error on /me: $1"],
    [/^AIAuto: બહુ ઝડપથી request \(rate limit\) — થોડી વાર પછી ટ્રાય કરો$/,
      "AIAuto: too many requests (rate limit) — try again shortly"],
    [/^AIAuto: 15 મિનિટમાં job પૂરું ન થયું — queue લાંબી હોઈ શકે, પછી ટ્રાય કરો$/,
      "AIAuto: the job did not finish in 15 minutes — the queue may be " +
      "long, try again later"],
    [/^AIAuto પ્લેટફોર્મ સાથે કનેક્ટ ન થયું — સર્વર ચાલુ છે\? URL\/key બરાબર છે\? \(સેટિંગ → AI તસવીર\)(.*)$/,
      "Could not connect to the AIAuto platform — is the server running? " +
      "Are the URL and key right? (Settings → AI Images)$1"],
    [/^\(જ્યાં જોડાવા ગયું: (.+)\)$/, "(tried to connect to: $1)"],
    [/^Pollinations સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો, કે થોડી વારે ફરી ટ્રાય કરો\.$/,
      "Could not reach Pollinations — check your internet, or try again " +
      "in a moment."],
    [/^Google Gemini સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો\.$/,
      "Could not reach Google Gemini — check your internet."],
    [/^OpenAI સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો\.$/,
      "Could not reach OpenAI — check your internet."],
    [/^⚠️ Key માં ઈમોજી\/space જેવો કચરો હતો — સાફ કરીને વાપર્યો\. સેટિંગમાં ફક્ત ak_\.\.\. વાળો key જ પેસ્ટ કરો\.$/,
      "⚠️ The key had junk (emoji/space) in it — cleaned before use. " +
      "Paste only the ak_... key in Settings."],
    [/^⚠️ AI Newsroom ભૂલ:$/, "⚠️ AI Newsroom error:"],
    [/^⚠️ 127\.0\.0\.1 એટલે 'આ જ કોમ્પ્યુટર'\. AIAuto જો બીજા કોમ્પ્યુટર પર ચાલે છે તો એનું સાચું IP લખો — (.*)$/,
      "⚠️ 127.0.0.1 means \"this very computer\". If AIAuto runs on " +
      "another machine, enter its real IP — $1"],
    [/^એ કોમ્પ્યુટર ચાલુ છે\? AIAuto ચાલુ છે\? એક જ WiFi\/નેટવર્ક પર છો\? Firewall બંધ છે\?$/,
      "Is that computer on? Is AIAuto running? Are you on the same " +
      "WiFi/network? Is the firewall off?"]
  ];

  function norm(s) { return s.replace(/\s+/g, " ").trim(); }

  var MAP = {};
  for (var k in D) MAP[norm(k)] = D[k];

  function t(raw) {
    var s = norm(raw);
    if (!s) return null;
    if (MAP[s] !== undefined) return MAP[s];
    for (var i = 0; i < R.length; i++) {
      if (R[i][0].test(s)) return s.replace(R[i][0], R[i][1]);
    }
    return null;
  }

  /* ── DOM અનુવાદ ─────────────────────────────────────────────── */
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1 };
  var ATTRS = ["placeholder", "title", "aria-label"];

  function walk(root) {
    if (root.nodeType === 1) {
      var els = root.querySelectorAll ? root.querySelectorAll("*") : [];
      for (var i = -1; i < els.length; i++) {
        var el = i < 0 ? root : els[i];
        if (el.nodeType !== 1) continue;
        for (var a = 0; a < ATTRS.length; a++) {
          var v = el.getAttribute && el.getAttribute(ATTRS[a]);
          if (v) { var e = t(v); if (e) el.setAttribute(ATTRS[a], e); }
        }
      }
    }
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var n, todo = [];
    while ((n = w.nextNode())) {
      if (n.parentNode && SKIP[n.parentNode.nodeName]) continue;
      var en = t(n.nodeValue);
      if (en !== null && en !== norm(n.nodeValue)) todo.push([n, en]);
    }
    for (var j = 0; j < todo.length; j++) todo[j][0].nodeValue = todo[j][1];
  }

  var obs = null;
  function translateAll(root) {
    if (obs) obs.disconnect();
    try { walk(root || document.body); } catch (e) { /* ચૂપચાપ */ }
    if (obs) obs.observe(document.body, { childList: true, subtree: true,
                                          characterData: true });
  }

  /* ── ભાષા બટન ───────────────────────────────────────────────── */
  function makeBtn(id, css) {
    var b = document.createElement("button");
    b.id = id;
    b.className = "ghost";
    b.style.cssText = css;
    b.textContent = LANG === "en" ? "🌐 ગુજરાતીમાં જુઓ" : "🌐 View in English";
    b.onclick = function () {
      localStorage.setItem("ui_lang", LANG === "en" ? "gu" : "en");
      location.reload();
    };
    return b;
  }

  function addToggle() {
    // સાઈડબારમાં (કોમ્પ્યુટર)
    var side = document.querySelector(".side-status");
    if (side && !document.getElementById("lang-toggle"))
      side.appendChild(makeBtn("lang-toggle", "width:100%;margin-top:6px"));
    // સેટિંગ પેજમાં — મોબાઈલમાં સાઈડબાર દેખાતું નથી
    var head = document.querySelector("#tab-settings .topline");
    if (head && !document.getElementById("lang-toggle-2"))
      head.appendChild(makeBtn("lang-toggle-2", "margin-left:auto"));
  }

  /* alert/confirm માં પણ અંગ્રેજી — એ DOM માં નથી હોતા */
  function wrapDialogs() {
    ["alert", "confirm", "prompt"].forEach(function (fn) {
      var orig = window[fn].bind(window);
      window[fn] = function (msg) {
        var s = String(msg == null ? "" : msg);
        var out = s.split("\n").map(function (line) {
          return t(line) !== null ? t(line) : line;
        }).join("\n");
        return arguments.length > 1
          ? orig(out, arguments[1]) : orig(out);
      };
    });
  }

  function start() {
    addToggle();
    if (LANG !== "en") return;
    document.documentElement.lang = "en";
    wrapDialogs();
    translateAll(document.body);
    obs = new MutationObserver(function (recs) {
      var roots = [];
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        if (r.type === "characterData") roots.push(r.target.parentNode || r.target);
        for (var j = 0; j < r.addedNodes.length; j++) roots.push(r.addedNodes[j]);
      }
      if (!roots.length) return;
      obs.disconnect();
      for (var k = 0; k < roots.length; k++) {
        if (roots[k] && roots[k].nodeType === 1) { try { walk(roots[k]); } catch (e) {} }
        else if (roots[k] && roots[k].nodeType === 3) {
          var en = t(roots[k].nodeValue);
          if (en !== null) roots[k].nodeValue = en;
        }
      }
      obs.observe(document.body, { childList: true, subtree: true,
                                   characterData: true });
    });
    obs.observe(document.body, { childList: true, subtree: true,
                                 characterData: true });
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();

  window.I18N = { lang: LANG, t: t, translate: translateAll };
})();
