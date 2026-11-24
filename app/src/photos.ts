// Zdjęcia kategorii na kartach (wygenerowane w Canvie, nasze). Zasady:
// 0) konkretne miejsce (Burj Khalifa, Louvre, Miracle Garden...) ma pierwszeństwo,
// 1) rodzaj eventu po słowach w tytule (rower → rower, bieg → bieganie...), 2) inaczej kategoria,
// 3) zdjęcia z widokiem konkretnego miasta tylko dla tego miasta, 4) ten sam wpis = zawsze to samo zdjęcie,
// 5) sąsiednie karty dostają różne wersje, gdy jest z czego wybierać.
import { Item } from './logic';
import { PHOTO_FILES } from './photos.gen';

// Konkretne miejsca (najważniejsze): event/miejsce/oferta w tym miejscu dostaje zdjęcie tego miejsca (klucz lm_*).
// Sprawdzane w tytule i w miejscu. Działa dopiero, gdy jest plik assets/photos/lm_<nazwa>-<n>.jpg.
const LANDMARKS: [RegExp, string][] = [
  [/burj khalifa|at the top\b|dubai fountain/i, 'lm_burj_khalifa'],
  [/louvre/i, 'lm_louvre'],
  [/miracle garden/i, 'lm_miracle_garden'],
  [/grand mosque|sheikh zayed mosque/i, 'lm_grand_mosque'],
  [/etihad arena/i, 'lm_etihad_arena'],
  [/coca[- ]?cola arena/i, 'lm_coca_cola_arena'],
  [/dubai opera/i, 'lm_dubai_opera'],
  [/madinat jumeirah|souk madinat/i, 'lm_madinat'],
  [/expo city|al wasl dome|al wasl plaza/i, 'lm_expo_city'],
  [/palm jumeirah|\bthe palm\b|atlantis/i, 'lm_palm'],
  [/arts cent(er|re).*nyu|nyuad arts|(blue hall|red theat(er|re)|black box|east plaza).*nyu/i, 'lm_nyuad'],
  [/saadiyat/i, 'lm_saadiyat'],
  [/polonia (polish|restaurant)|poloniadubai/i, 'lm_polonia'],
  [/reem island|\bal reem\b|reem mall|shams abu dhabi|gate towers|reem central park/i, 'lm_reem'],
  [/corniche/i, 'lm_corniche'],
  [/museum of the future/i, 'lm_museum_future'],
  [/global village/i, 'lm_global_village'],
  [/yas marina circuit/i, 'lm_yas_marina_circuit'],
  [/qasr al watan/i, 'lm_qasr_al_watan'],
  [/dubai frame/i, 'lm_dubai_frame'],
  [/burj al arab/i, 'lm_burj_al_arab'],
  [/ain dubai/i, 'lm_ain_dubai'],
  [/jebel jais/i, 'lm_jebel_jais'],
  // dzielnice z widokiem (tylko miejsca i hotelowe day pass / staycation): hotel w Downtown -> widok na Burj, w Marinie -> Marina
  [/downtown dubai|business bay|dubai mall|address (downtown|boulevard|sky view|dubai mall)|vida downtown|palace downtown|armani hotel|burj (park|views)|souk al bahar|opera district/i, 'lm_downtown'],
  [/dubai marina|\bjbr\b|jumeirah beach residence|the walk\b|bluewaters|marina (mall|walk) dubai|dubai harbour/i, 'lm_marina'],
  [/yas island|yas bay|yas mall|yas plaza|yas links|yas beach/i, 'lm_yas'],
  [/al maryah|galleria (mall|island)|maryah island/i, 'lm_maryah'],
  [/al seef|dubai creek|creek harbour|festival city|deira creek|al jaddaf/i, 'lm_creek'],
  [/al majaz|al qasba|al noor island|khalid lagoon|buhaira corniche/i, 'lm_sharjah_water'],
  [/jebel hafeet|jabal hafeet/i, 'lm_jebel_hafeet'],
  [/al marjan|marjan island/i, 'lm_marjan'],
];

const AREAS = new Set(['lm_palm', 'lm_saadiyat', 'lm_corniche', 'lm_reem', 'lm_downtown', 'lm_marina', 'lm_yas', 'lm_maryah', 'lm_creek', 'lm_sharjah_water', 'lm_jebel_hafeet', 'lm_marjan']);
const VENUES = new Set(['lm_etihad_arena', 'lm_coca_cola_arena', 'lm_dubai_opera', 'lm_nyuad', 'lm_expo_city', 'lm_louvre', 'lm_museum_future']);

const RULES: [RegExp, string][] = [
  [/bungee/i, 'bungee'],
  // miejsca o konkretnym charakterze: bez własnego zdjęcia lepiej ikonka niż obce (kolejka górska przy akwarium)
  [/aquarium|dolphin|sea ?world|underwater zoo/i, 'aquarium'],
  [/\bzoo\b|safari park|sharjah safari|crocodile|wildlife park|green planet|butterfly garden/i, 'zoo'],
  [/water ?park|waterworld|aquaventure|wild wadi|aqua ?park|laguna|montazah/i, 'waterpark'],
  [/observation deck|sky views|at the top|the view at|\bview(ing)? deck/i, 'viewpoint'],
  [/\bmosque\b/i, 'mosque'],
  [/legoland/i, 'legoland'],
  [/warner bros|img worlds|ferrari world|motiongate|theme park|real madrid world/i, 'attractions'],
  [/trampoline|bounce|flip ?out|air maniax/i, 'trampoline'],
  [/ninja|tepfactor|ropes course|aventura|high ropes/i, 'active'],
  [/aviation|skydiv|parachut|paraglid|paramotor|gyrocopter|balloon flight|hot air balloon|seaplane|helicopter|microlight|zip ?line|xline|\bifly\b|jais flight|aerobatic|flying (lesson|experience)|scenic flight/i, 'flying'],
  [/\bski\b|ski dubai|snow abu dhabi|snow park|ice rink|ice skating|on ice\b/i, 'snow'],
  [/ceramic|pottery|sculpt|\bclay\b/i, 'studios'],
  [/painting|paint (and|&) sip|\bpaints?\b|art (class|studio|workshop)|art cent(re|er)|calligraph|drawing|\bdraw\b|sketch|watercolou?r|printmaking|al marsam/i, 'painting'],
  [/cooking|chocolate(?! factory)|baking|\bbake\b|gingerbread|culinary|top chef/i, 'cooking'],
  [/board ?gam|boardgam|game night|\bchess\b|mahjong|scrabble|clocktower|polyglot|language exchange|language & culture|conversation (club|meetup|café|cafe)|conversations over coffee/i, 'community'],
  [/\bdance\b|dancing|salsa|bachata|kizomba|tango|heels|twerk|afrobeats dance|hip ?hop class|zumba|belly ?dance|riverdance/i, 'dance'],
  [/aqua ?fit|aqua ?aerobic|aqua ?zumba|water aerobic|aqua ?gym/i, 'aquafit'],
  [/kayak|paddle ?board|\bsup\b|jet ?ski|wakeboard|kite ?surf|\bsurf(ing|board)?\b(?! club)|scuba|diving|deep dive|snorkel|flyboard|sail ?gp|sail grand prix|regatta|sailing (?!the)|rowing/i, 'watersports'],
  [/\bcandlelight\b|orchestra|symphon|philharmon|quartet|classical|(?<!of the )opera\b|recital|piano|violin/i, 'candlelight'],
  [/comedy|stand[- ]?up|comedian/i, 'comedy'],
  [/theat(re|er)|playhouse|phantom of the opera|chocolate factory|musical\b|ballet|\bplay\b(?! ?(&|and) feast| area)|pantomime|swan lake|nutcracker|kids'? show|storytelling|live on stage|puppet|magic show/i, 'theatre'],
  [/cinema|film|screening|movie/i, 'cinema'],
  [/\bjazz\b/i, 'jazz'],
  [/\bdj\b|techno|afro ?house|\bedm\b|\brave\b|club night/i, 'dj'],
  [/arabic music|tarab|\boud\b(?! exhibition| and perfume|.*perfume)|khaleeji|eid concert/i, 'arabic'],
  [/rock republic|climbing|bouldering/i, 'active'],
  [/\brock\b|\bmetal\b|\bpunk\b/i, 'rock'],
  [/horse|equestrian|racecourse|endurance ride|show jumping|polo\b/i, 'horse'],
  [/cycl|\bbike ride|\bbicycle|velo\b/i, 'cycling'],
  [/swim|triathlon|aquathlon|open water/i, 'swimming'],
  [/\brun\b|running|marathon|\b(3|5|10|21)k\b|\d+ ?km\b|parkrun|race run|trail race|relay/i, 'running'],
  [/tennis|padel|squash|pickleball/i, 'padel'],
  [/yoga|pilates|meditat(e|ion\b|ing)|breathwork|sound bath|sound healing/i, 'yoga'],
  [/bootcamp|hiit|workout|fitness|crossfit|strength training|circuit training/i, 'fitness'],
  [/cricket|\bt10\b|\bt20\b|ilt20|knight riders|dubai capitals|desert vipers|gulf giants|mi emirates|sharjah warriorz/i, 'cricket'],
  [/football|soccer|super cup|\bfc\b|pro league|manchester city/i, 'football'],
  [/golf/i, 'golf'],
  [/desert challenge|\brally\b|\bbaja\b|dakar rally|rally dakar|off-?road|dune bash|drift(?! beach)/i, 'rally'],
  [/car show|car and bike|bike week|custom show|car meet/i, 'carshow'],
  [/grand prix|formula|\bf1\b|motor|karting|kartdrome|autodrome|nitro circus|driving experience/i, 'motorsport'],
  [/\bcamels?\b/i, 'camel'],
  [/karaoke/i, 'night_out'],
  [/\bquiz\b/i, 'quiz'],
  [/\bbooks?\b|book (club|fair|launch|presentation)|library|reading|poetry/i, 'books'],
  [/\btalk\b|lecture|panel|in conversation|seminar/i, 'talk'],
  [/night market|flea|bazaar|farmers'? market|winter market|christmas market|craft market|food market|urban market|souq|souk/i, 'market'],
  [/workshop|arts (and|&) crafts|craft/i, 'workshop'], // ogólne warsztaty – po tańcu, jodze itd.
  [/frieze|art fair|art week|art dubai|art abu dhabi|abu dhabi art|art exhibition|gallery|alserkal|jameel arts|421 arts|art foundation|art museum|tashkeel/i, 'artfair'],
  [/teamlab|immersive|digital art|museum|art gallery|biennial/i, 'museums'],
  // na końcu: bieg w parku archeologicznym to nadal bieg
  [/heritage village|heritage area|old village|pearling village|abandoned village|\bfort\b|castle|archaeolog|ruins|mud ?brick|historic (district|site|neighbourhood)|al fahidi|al bastakiya|heart of sharjah|qasr al hosn|\bhisn\b/i, 'heritage'],
  // jedzenie i święta (event: brunch świąteczny, kolacja sylwestrowa) – przed plażą/farmą na końcu
  [/new year|\bnye\b|hogmanay/i, 'nye'],
  [/\bbrunch\b(?! that burns)/i, 'brunch'],
  [/breakfast/i, 'breakfast'],
  [/dinner|buffet|\blunch\b|sunday roast|\broast\b|tasting menu|by the course|set menu|thanksgiving|turkey|iftar|suhoor/i, 'dinner'],
  [/christmas|xmas|santa|festive|advent|gingerbread/i, 'xmas'],
  [/\bexpo\b|trade (show|fair)|summit|conference|\bforum\b|(international|games|food|jewell?ery|perfumes?|watch|boat|motor|hunting)\b.*\b(exhibition|show)\b/i, 'expo'],
  [/concert|world tour/i, 'concert'],
  // na samym końcu, tylko gdy nic innego nie pasuje (koncert na plaży to koncert)
  [/\bfarm\b|oasis|\babra\b/i, 'farm'],
  [/al qudra|love lake/i, 'lakes'],
  [/desert (safari|reserve|conservation|park)|marmoom|sand ?dunes|dune bash|liwa(?!\))/i, 'nature'],
  [/jebel|hatta|\bwadi\b|mountain|mubazzarah/i, 'daytrips'],
  [/\bbeach\b(?! hotel)/i, 'beaches'],
];

// kategoria (events/places/deals) → klucz zdjęć; sport bez rodzaju → pula różnych sportów
const CAT: Record<string, string[]> = {
  comedy: ['comedy'], music: ['music'], culture: ['culture'], sport: ['sport'], food: ['food'],
  festivals: ['festivals'], festival: ['festivals'], nightlife: ['nightlife'], classes: [], nature: ['nature'],
  community: ['community'], business: ['talk'], family: ['family'], market: ['market'],
  beaches: ['beaches'], parks: ['parks'], museums: ['museums'], attractions: [], active: [],
  kids: ['kids'], markets: ['souk'], studios: [], daytrips: [],
  day_pass: ['day_pass'], ladies_night: ['ladies_night'], brunch: ['brunch'], happy_hour: ['happy_hour'], night_out: ['night_out'], lunch: ['lunch'],
  dinner: ['dinner'], quiz: ['quiz'], breakfast: ['breakfast'], staycation: ['staycation'],
};

// Zdjęcia z widokiem miasta: klucz_miasto (np. day_pass_dubai) – dodawane do puli tylko w tym mieście.
const CITY_SUFFIX: Record<string, string> = { Dubai: 'dubai', 'Abu Dhabi': 'abudhabi', Sharjah: 'sharjah', 'Ras Al Khaimah': 'rak' };
// ...i tylko w dzielnicach, z których ten widok jest prawdziwy (Yas, Saadiyat, Hatta itd. nie dostają panoramy Corniche/Marina).
const SKYLINE_ZONES: Record<string, Set<string> | null> = {
  'Abu Dhabi': new Set(['corniche', 'bateen', 'downtown', 'maryah', 'reem', 'mina']),
  Dubai: new Set(['dxb_marina', 'dxb_palm', 'dxb_downtown', 'dxb_jumeirah', 'dxb_creek', 'dxb_oldtown']),
  Sharjah: new Set(['shj_center', 'shj_heritage']),
  'Ras Al Khaimah': null, // całe miasto
};

// Gdy wpis pasuje do tych rodzajów, a zdjęcia jeszcze nie ma: lepiej ikonka niż obce zdjęcie z kategorii.
const NO_FALLBACK = new Set(['legoland', 'trampoline', 'lakes', 'rally', 'carshow', 'aquafit', 'painting', 'cooking', 'workshop', 'aquarium', 'zoo', 'waterpark', 'viewpoint', 'mosque', 'farm', 'bungee', 'flying', 'watersports', 'heritage', 'dance', 'snow']);

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

function pool(item: Item): number[] {
  let keys: string[] | undefined;
  const placeText = `${(item.rawTitle ?? item.title)} ${item.where ?? ''} ${item.event?.venue ?? ''}`;
  // Polonia (polska restauracja): oferty i eventy tam -> polskie dania (pierogi, schabowy), miejsce -> szyld + polskie dania
  if (/polonia|polish (cuisine|restaurant|food)|pierogi/i.test(placeText) && PHOTO_FILES.polish_food) {
    return item.kind === 'place' ? [...(PHOTO_FILES.lm_polonia ?? []), ...PHOTO_FILES.polish_food] : [...PHOTO_FILES.polish_food];
  }
  let lm = LANDMARKS.find(([re]) => re.test(placeText));
  // Całe dzielnice/wyspy (Palm, Saadiyat, Corniche, Reem): ich zdjęcie tylko dla miejsc. Event albo oferta w hotelu
  // na Palmie dostaje zdjęcie swojego rodzaju (koncert, brunch), a nie widok wyspy z lotu ptaka.
  // Wyjątek: hotelowy day pass / staycation w dzielnicy z widokiem dostaje widok (Burj, Marina) obok zdjęć day passu.
  const hotelDeal = item.kind === 'deal' && (item.catKey === 'day_pass' || item.catKey === 'staycation');
  // Miejsce w dzielnicy z widokiem (np. muzeum albo pracownia na Saadiyat): widok wyspy/plaży tylko dla plaż i miejsc
  // bez własnego rodzaju zdjęcia. Muzeum dostaje zdjęcie muzeum, pracownia ceramiki – ceramikę.
  if (lm && AREAS.has(lm[1]) && item.kind === 'place' && item.catKey !== 'beaches') {
    const t = RULES.find(([re]) => re.test(item.rawTitle ?? item.title));
    if (t && PHOTO_FILES[t[1]]) return [...PHOTO_FILES[t[1]]];
    if ((CAT[item.catKey] ?? []).some((k) => PHOTO_FILES[k])) lm = undefined;
  }
  if (lm && AREAS.has(lm[1]) && (!PHOTO_FILES[lm[1]] || (item.kind !== 'place' && !hotelDeal))) lm = undefined;
  if (lm && hotelDeal && AREAS.has(lm[1])) return [...PHOTO_FILES[lm[1]], ...(PHOTO_FILES[item.catKey] ?? [])];
  // Oferty (ladies night, brunch, quiz) w znanym miejscu: zdjęcie rodzaju oferty. Budynek tylko dla staycation / day pass.
  if (lm && item.kind === 'deal' && item.catKey !== 'staycation' && item.catKey !== 'day_pass' && CAT[item.catKey]) lm = undefined;
  // Areny i sale (Etihad Arena, Coca-Cola Arena, Opera...): event z rozpoznanym rodzajem (komedia, koncert DJ, teatr)
  // dostaje zdjęcie rodzaju, a zdjęcie budynku tylko gdy rodzaju nie widać – żeby wieczór w arenie nie miał 5 takich samych kart.
  // Rodzaj z tytułu wygrywa ze znanym miejscem (Kayaking at Louvre -> kajaki, Swan Lake w Operze -> teatr).
  // (nazwę samego miejsca wycinamy z tytułu, żeby "Museum of the Future" nie stało się zwykłym "museum")
  const rest = lm ? (item.rawTitle ?? item.title).replace(new RegExp(lm[0].source, 'gi'), ' ') : (item.rawTitle ?? item.title);
  const typeHit = item.kind !== 'deal' && lm ? RULES.find(([re]) => re.test(rest)) : undefined;
  if (typeHit && PHOTO_FILES[typeHit[1]]) return [...PHOTO_FILES[typeHit[1]]];
  // event w arenie bez rozpoznanego rodzaju: wnętrze tej areny (lm_<arena>_in) + jej zdjęcia z zewnątrz
  if (lm && item.kind === 'event' && VENUES.has(lm[1])) {
    const both = [...(PHOTO_FILES[`${lm[1]}_in`] ?? []), ...(PHOTO_FILES[lm[1]] ?? [])];
    return both;
  }
  if (lm) return PHOTO_FILES[lm[1]] ? [...PHOTO_FILES[lm[1]]] : []; // znane miejsce bez zdjęcia: ikonka, nie obce zdjęcie
  if (item.kind !== 'deal' || !item.catKey || item.catKey === 'other') {
    const hit = RULES.find(([re]) => re.test((item.rawTitle ?? item.title)));
    if (hit && PHOTO_FILES[hit[1]]) keys = [hit[1]];
    else if (hit && NO_FALLBACK.has(hit[1])) return [];
  }
  // Event bez rozpoznanego rodzaju z tytułu: ikonka zamiast ogólnego zdjęcia kategorii (to ono dawało złe zdjęcia).
  // wyjątek: event muzyczny bez rodzaju dostaje ogólne zdjęcie sceny koncertowej (gdy już jest)
  if (!keys && item.kind === 'event') {
    if (item.catKey === 'music' && PHOTO_FILES.concert) keys = ['concert'];
    else return [];
  }
  if (!keys) keys = CAT[item.catKey] ?? [];
  const zones = SKYLINE_ZONES[item.city];
  const suf = zones === null || (zones && item.zone && zones.has(item.zone)) ? CITY_SUFFIX[item.city] : undefined;
  const out: number[] = [];
  for (const k of keys) {
    out.push(...(PHOTO_FILES[k] ?? []));
    if (suf) out.push(...(PHOTO_FILES[`${k}_${suf}`] ?? []));
  }
  return out;
}

/** Zdjęcie dla karty albo null (wtedy karta pokazuje ikonkę). `avoid` = zdjęcie poprzedniej karty. */
export function photoFor(item: Item, avoid?: number | null): number | null {
  const p = pool(item);
  if (!p.length) return null;
  let i = hash(item.key) % p.length;
  if (p.length > 1 && p[i] === avoid) i = (i + 1) % p.length;
  return p[i];
}
