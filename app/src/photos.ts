// Zdjęcia kategorii na kartach (wygenerowane w Canvie, nasze). Zasady:
// 0) konkretne miejsce (Burj Khalifa, Louvre, Miracle Garden...) ma pierwszeństwo,
// 1) rodzaj eventu po słowach w tytule (rower → rower, bieg → bieganie...), 2) inaczej kategoria,
// 3) zdjęcia z widokiem konkretnego miasta tylko dla tego miasta, 4) ten sam wpis = zawsze to samo zdjęcie,
// 5) sąsiednie karty dostają różne wersje, gdy jest z czego wybierać.
import { Item } from './logic';
import { PHOTO_OFF } from './photoOff';
import { PHOTO_FILES, PHOTO_NAMES } from './photos.gen';

// Klucz 'community' miesza zdjęcia: gra planszowa / spotkanie w kawiarni oraz sprzątanie plaży (community-2, -4).
// Sprzątanie tylko dla akcji sprzątania; gry planszowe tylko zdjęcie z grą (zgłoszenie 27.11.2026: sprzątanie plaży przy grach w Luwrze).
{
  const byName = (re: RegExp) => (PHOTO_FILES.community ?? []).filter((f) => re.test(PHOTO_NAMES.get(f) ?? ''));
  const clean = new Set([...byName(/^community-(2|4)$/)]);
  (PHOTO_FILES as Record<string, number[]>).cleanup = [...clean];
  (PHOTO_FILES as Record<string, number[]>).boardgames ??= byName(/^community-1$/);
  (PHOTO_FILES as Record<string, number[]>).community = (PHOTO_FILES.community ?? []).filter((f) => !clean.has(f));
}

// Konkretne miejsca (najważniejsze): event/miejsce/oferta w tym miejscu dostaje zdjęcie tego miejsca (klucz lm_*).
// Sprawdzane w tytule i w miejscu. Działa dopiero, gdy jest plik assets/photos/lm_<nazwa>-<n>.jpg.
const LANDMARKS: [RegExp, string][] = [
  [/burj khalifa|at the top\b|dubai fountain/i, 'lm_burj_khalifa'],
  [/louvre/i, 'lm_louvre'],
  [/miracle garden/i, 'lm_miracle_garden'],
  // zgłoszenia Agi 27.11: konkretne miejsca dostają własny klucz (prawdziwe zdjęcie albo ikonka), a nie zdjęcie okolicy
  [/twiggy/i, 'day_pass'],
  [/xline|zip ?line/i, 'zipline'],
  [/madame tussauds|wax museum/i, 'waxmuseum'],
  [/sheikh mohammed centre for cultural|\bsmccu\b|coffee museum|al fahidi|al bastakiya|bastakiya/i, 'lm_al_fahidi'],
  [/sharjah mosque/i, 'lm_sharjah_mosque'],
  [/sheikh khalifa (bin zayed )?(al nahyan )?mosque|al ain grand mosque/i, 'lm_khalifa_mosque'],
  [/al majaz waterfront/i, 'lm_al_majaz'],
  [/grand mosque|sheikh zayed mosque/i, 'lm_grand_mosque'],
  [/etihad arena/i, 'lm_etihad_arena'],
  [/coca[- ]?cola arena/i, 'lm_coca_cola_arena'],
  [/dubai opera/i, 'lm_dubai_opera'],
  [/madinat jumeirah|souk madinat/i, 'lm_madinat'],
  [/expo city|al wasl dome|al wasl plaza/i, 'lm_expo_city'],
  [/aura sky ?pool/i, 'lm_aura'],  // basen na 50. piętrze, nie plaża (zgłoszenie 26.11); bez zdjęcia = ikonka
  [/palm jumeirah|\bthe palm\b|atlantis/i, 'lm_palm'],
  [/arts cent(er|re).*nyu|nyuad arts|(blue hall|red theat(er|re)|black box|east plaza).*nyu/i, 'lm_nyuad'],
  [/teamlab/i, 'immersive'],  // teamLab na Saadiyat: sztuka cyfrowa, nie plaża Saadiyat (kontrola zdjęć 27.11)
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
  [/jebel jais|\bjais\b/i, 'lm_jebel_jais'],
  [/khor ?fakkan amphitheat|khor ?fakkan waterfall/i, 'lm_khorfakkan_amph'],
  // prawdziwe zdjęcia od testerki Agi (27.11.2026)
  [/jaz[ie]+ra(h)? al hamra heritage|al jazeera al hamra( heritage village)?|jazirat al hamra (heritage|village)|abandoned (pearling )?village/i, 'lm_jazeera_hamra'],
  [/national museum of ras al khaimah|ras al khaimah national museum|rak national museum/i, 'lm_rak_museum'],
  [/al suhub/i, 'lm_suhub'],
  [/al rafisah/i, 'lm_rafisah'],
  [/khor ?fakkan beach/i, 'lm_khorfakkan_beach'],
  [/\bal rams\b|\brams (beach|village|coast)/i, 'lm_rams'],
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

const AREAS = new Set(['lm_rams', 'lm_palm', 'lm_saadiyat', 'lm_corniche', 'lm_reem', 'lm_downtown', 'lm_marina', 'lm_yas', 'lm_maryah', 'lm_creek', 'lm_sharjah_water', 'lm_jebel_hafeet', 'lm_marjan']);
const VENUES = new Set(['lm_etihad_arena', 'lm_coca_cola_arena', 'lm_dubai_opera', 'lm_nyuad', 'lm_expo_city', 'lm_louvre', 'lm_museum_future']);

const RULES: [RegExp, string][] = [
  // wszystko na Jebel Jais (park linowy, taras, tyrolka, sanki) pokazuje góry Jais, nie halę wspinaczkową ani miasto
  [/\bjais\b/i, 'lm_jebel_jais'],
  [/bungee/i, 'bungee'],
  // miejsca o konkretnym charakterze: bez własnego zdjęcia lepiej ikonka niż obce (kolejka górska przy akwarium)
  [/aquarium|dolphin|sea ?world|underwater zoo/i, 'aquarium'],
  [/\bzoo\b|safari park|sharjah safari|crocodile|wildlife park|green planet|butterfly garden/i, 'zoo'],
  [/water ?park|waterworld|aquaventure|wild wadi|aqua ?park|laguna|montazah/i, 'waterpark'],
  // taras widokowy w wieżowcu (panorama miasta); górskie punkty widokowe (Jais, Hafeet, Hatta) dostają zdjęcie gór, nie miasta
  [/^(?!.*\b(jais|jebel|jabal|mountain|hatta|hafeet|wadi|khor ?fakkan)\b).*(observation deck|sky views|at the top|the view at|\bview(ing)? deck)/i, 'viewpoint'],
  [/\bmosque\b/i, 'mosque'],
  [/legoland/i, 'legoland'],
  [/warner bros|img worlds|ferrari world|motiongate|theme park|real madrid world/i, 'attractions'],
  [/trampoline|bounce|flip ?out|flipped park|air maniax/i, 'trampoline'],  // Flip Junior (Flipped Park RAK) dostawał basen na pustyni (tester 27.11)
  [/aventura|ropes course|high ropes|treetop|tree top/i, 'ropes'],  // park linowy na drzewach, nie hala (Aga 27.11)
  [/ninja|tepfactor/i, 'active'],
  // zjazd na linie i skoki to nie samolot nad wydmami (XLine Dubai Marina – Aga 27.11)
  [/zip ?line|xline|jais flight|jais sledder/i, 'zipline'],
  [/skydiv|\bifly\b|indoor skydiving|parachut/i, 'skydive'],
  [/hot air balloon|balloon (flight|ride)/i, 'balloon'],
  [/aviation|skydiv|parachut|paraglid|paramotor|gyrocopter|balloon flight|hot air balloon|seaplane|helicopter|microlight|zip ?line|xline|\bifly\b|jais flight|aerobatic|air ?show|flying (lesson|experience)|scenic flight/i, 'flying'],
  // lodowisko to nie stok narciarski (Dubai Ice Rink dostawał Ski Dubai – tester 27.11): własne zdjęcie albo ikonka
  [/ice rink|ice skating|skating rink/i, 'ice_rink'],
  // spotkanie z Mikołajem: zdjęcie z Mikołajem, nie stok miejsca (zgłoszenie 27.11 „Meet Santa at Snow Abu Dhabi”); do tego czasu ikonka
  // sztuka cyfrowa / immersyjna (teamLab, Infinity des Lumières, ToDA, Museum of Illusions): nie sala z gablotami ani scena teatru (kontrola zdjęć 27.11)
  [/teamlab|infinity des lumi|^theatre of digital art|museum of illusions|immersive (art|exhibition|experience)|digital art/i, 'immersive'],
  // pokaz taneczny na scenie (balet, hip-hop, Riverdance): scena, nie para tańcząca salsę (kontrola zdjęć 27.11)
  [/ballet|ballerina|riverdance|hip[- ]?hop (dance|show|theat)|street dance|dance (show|performance|gala|company|theatre)|boy blue|this is michael|face aux murs|cie hors/i, 'theatre'],
  // zwierzęta inne niż sawanna: motyle, krokodyle, las deszczowy – ikonka, dopóki nie ma zdjęcia
  [/butterfl/i, 'butterfly'], [/crocodile/i, 'crocodile'], [/green planet|rainforest/i, 'rainforest'],
  [/time out market|food hall/i, 'food'],
  [/meet(ing)? santa|santa'?s? (grotto|house|village|visit|meet)|(with|visit|photos? with) santa|santa claus/i, 'santa'],
  [/\bski\b|ski dubai|snow abu dhabi|snow park/i, 'snow'],
  // twarze malowane dzieciom to nie malowanie na sztalugach (Splash Park Face Painting, tester 26.11)
  [/face ?paint/i, 'facepaint'],
  // „sculpt” tylko jako zajęcia; wystawa rzeźby (Alfred Basbous: Sculpting the Line) to nie koło garncarskie
  [/ceramic|pottery|sculpt\w* (class|workshop|course|session)|\bclay\b/i, 'studios'],
  [/painting|paint (and|&) sip|\bpaints?\b|art (class|studio|workshop)|art cent(re|er)|calligraph|drawing|\beasel\b|\bdraw\b|sketch|watercolou?r|printmaking|al marsam/i, 'painting'],
  [/cooking|chocolate(?! factory)|baking|\bbake\b|gingerbread|culinary|top chef/i, 'cooking'],
  // gry planszowe: własne zdjęcie (stół z grami), do tego czasu ikonka – zdjęcia 'community' pokazywały sprzątanie plaży (zgłoszenie 27.11)
  [/clean[- ]?up|cleanup drive|litter pick|beach clean/i, 'cleanup'],
  [/board ?gam|boardgam|game night|\bchess\b|mahjong|scrabble|clocktower/i, 'boardgames'],
  [/polyglot|language exchange|language & culture|conversation (club|meetup|café|cafe)|conversations over coffee/i, 'community'],
  // ladies-only taniec: bez par z mężczyznami na zdjęciu (zgłoszenie testerki 26.11.2026) – własne zdjęcie albo ikonka
  // ladies night jako wydarzenie (duet w restauracji): zdjęcie ladies night, nie tłum na festiwalu (tester 26.11)
  [/ladies'? ?night/i, 'ladies_night'],
  // sport dla kobiet (Ladies Football, Women's Cycling): bez mężczyzn na zdjęciu – własne zdjęcie albo ikonka (tester 26.11)
  [/\b(ladies|women'?s?|girls)\b.*\b(football|soccer|cycling|cycle|cricket|basketball|volleyball|padel|tennis|run|running|boxing|swim)|\b(football|soccer|cycling|cricket|basketball|volleyball|padel|boxing)\b.*\b(ladies|women'?s?)\b/i, 'sport_ladies'],
  [/\b(ladies|women)[' ]*only\b.*\b(dance|dancing|heels|zumba|salsa|belly)\b|\b(dance|dancing|heels|zumba|salsa|belly)\b.*\b(ladies|women)[' ]*only\b/i, 'dance_ladies'],
  [/\bdance\b|dancing|\bdancers?\b|breakdanc|hip[- ]?hop (dance|crew|theat)|salsa|bachata|kizomba|tango|heels|twerk|afrobeats dance|hip ?hop class|zumba|belly ?dance|riverdance/i, 'dance'],
  [/aqua ?fit|aqua ?aerobic|aqua ?zumba|water aerobic|aqua ?gym/i, 'aquafit'],
  // namorzyny, mokradła, rezerwaty przyrody: własne zdjęcie (albo ikonka), nigdy miejski park z fontanną
  [/mangrove|wetland|nature reserve|bird sanctuary|flamingo/i, 'mangrove'],
  // wyścig żaglówek / dhow (Dubai Offshore Sailing Club) – nie paddleboard wśród namorzynów (tester 26.11)
  [/dhow (sailing )?race|sailing race|dhow sailing|offshore sailing|sail ?gp|sail grand prix/i, 'sailing'],  // SailGP: katamarany, nie paddleboard (tester 26.11)
  // wioślarstwo na ergometrach (Masfout X Indoor Rowing w siłowni) – nie kajaki (tester A 27.11)
  [/indoor rowing|rowing[\s\S]*\bgym\b|ergometer/i, 'fitness'],
  [/kayak|paddle ?board|\bsup\b|jet ?ski|wakeboard|kite ?surf|\bsurf(ing|board)?\b(?! club)|scuba|diving|deep dive|snorkel|flyboard|regatta|sailing (?!the)|rowing/i, 'watersports'],
  [/\bcandlelight\b|orchestra|symphon|philharmon|quartet|classical|\bbach\b|vivaldi|handel|mozart|beethoven|chopin|tchaikovsky|young maestro|(?<!of the )opera\b|recital|piano|violin/i, 'candlelight'],
  [/comedy|stand[- ]?up|comedian|laughter factory|exesanonymous|aakash gupta|mohamed helmy|biswa kalyan|max angioni|paul chowdhry|sapan verma|varun grover|gursimran khamba|angad ranyal|bader saleh|paul de saint sernin|trevor noah|max amini|nurlan saburov|whitney cummings|chai with chandan|steve harvey|apurva in emirates/i, 'comedy'],  // znani komicy bez słowa „comedy” w tytule (przegląd 26.11)
  [/theat(re|er)|playhouse|phantom of the opera|chocolate factory|musical\b(?! night| evening| show| fire)|ballet|on ice\b|\bplay\b(?! ?(&|and) feast| area| day)|pantomime|swan lake|nutcracker|kids'? show|storytelling|live on stage|puppet|magic show|(?<!nitro )circus|acrobat/i, 'theatre'],
  // kino plenerowe (plaża, dach, pod gwiazdami) -> zdjęcie pleneru; zwykły seans w sali -> sala kinowa (albo ikonka, póki zdjęcia nie ma)
  [/(outdoor|open.?air|beach|rooftop|drive.?in|under the stars|garden|park)\b.*(cinema|film|screening|movie)|(cinema|film|screening|movie).*\b(outdoor|open.?air|beach|rooftop|drive.?in|under the stars|garden|park)/i, 'cinema'],
  [/comic ?con\b/i, 'expo'],  // Film & Comic Con to targi, nie kino
  [/cinema|film|screening|movie/i, 'cinema_indoor'],
  [/\bjazz\b/i, 'jazz'],
  [/\bdj\b|\btechno\b|afro ?house|\bedm\b|\brave\b|club night|\bat (bohemia|be beach)\b|artbat|black coffee|ushua[iï]a|upperground/i, 'dj'],  // znani DJ-e i kluby DJ (ARTBAT w Ushuaïa, Black Coffee – zespół rockowy/wokalista, tester A 27.11)  // wieczory DJ w beach clubach: nie plaża
  [/arabic music|tarab|\boud\b(?! exhibition| and perfume|.*perfume)|khaleeji|eid concert/i, 'arabic'],
  [/rock republic|climbing|bouldering/i, 'active'],
  [/\brock\b|\bmetal\b|\bpunk\b/i, 'rock'],
  [/hunting (&|and) equestrian|hunting exhibition|adihex|aaihex/i, 'expo'],  // targi łowieckie, nie wyścigi konne
  // nauka jazdy konnej (Horse Riding Training Course w Mleiha) – nie wyścigi konne (tester 26.11)
  [/horse ?riding (lesson|course|training|class|session|experience)|riding (lesson|school|course)|horse ?back rid|horse riding\b(?!.*(race|cup|championship))/i, 'horseriding'],
  [/horse|equestrian|racecourse|endurance ride|show jumping|polo\b/i, 'horse'],
  [/cycling|cyclist|cycle (track|race|ride)|\bbike ride|\bbicycle|velo\b/i, 'cycling'],  // nie „Cycles” (spektakl)
  [/swim|triathlon|aquathlon|open water/i, 'swimming'],
  // bieg z przeszkodami (Spartan, Hurricane Heat, Tigers) – nie jezioro z flamingami w Al Qudra (tester 26.11)
  [/spartan|hurricane heat|obstacle (race|run|course)|tough mudder|tigers? obstacle/i, 'obstacle'],
  // bieg/duathlon w górach (Masfout, Hatta) – nie bieżnia nad morzem (Masfout Trail Run, tester A 27.11)
  [/\b(trail|duathlon|ultra|sky ?run)\b[\s\S]*\b(masfout|hatta|hajar|mountain|wadi|showka|mleiha)\b|\b(masfout|hatta|hajar|mountain)\b[\s\S]*\b(trail|run|duathlon|ultra)\b/i, 'trail_mountain'],
  [/\brun\b|running|marathon|\b(3|5|10|21)k\b|\d+ ?km\b|parkrun|race run|trail race|relay/i, 'running'],
  // tenis to nie padel (Dubai Duty Free Tennis Championships dostawał kort padla – tester A 27.11): własne zdjęcie albo ikonka
  [/tennis/i, 'tennis'],
  [/padel|squash|pickleball/i, 'padel'],
  // zawody kulturystyczne na scenie – nie trening na plaży (tester 26.11); po biegach („Run ... Bodybuilding Federation” to bieg)
  [/bodybuilding|physique|mr\.? olympia/i, 'bodybuilding'],
  [/yoga|pilates|meditat(e|ion\b|ing)|breathwork|sound bath|sound healing/i, 'yoga'],
  [/bootcamp|hiit|workout|fitness|crossfit|strength training|circuit training/i, 'fitness'],
  [/cricket|\bt10\b|\bt20\b|ilt20|knight riders|dubai capitals|desert vipers|gulf giants|mi emirates|sharjah warriorz/i, 'cricket'],
  [/football|soccer|super cup|\bfc\b|pro league|manchester city/i, 'football'],
  [/golf/i, 'golf'],
  // parada zabytkowych aut (Route 71 / Masar 71 Rally) – nie buggy na wydmach (tester A 27.11)
  [/classic cars?|vintage cars?|old cars?|masar 71|route 71/i, 'carshow'],
  [/desert challenge|\brally\b|\bbaja\b|dakar rally|rally dakar|off-?road|dune bash|drift(?! beach)/i, 'rally'],
  [/car show|motor show|auto show|car and bike|bike week|custom show|car meet/i, 'carshow'],
  [/grand prix|formula|\bf1\b|motor|karting|kartdrome|autodrome|nitro circus|driving experience/i, 'motorsport'],
  [/\bcamels?\b/i, 'camel'],
  [/karaoke/i, 'night_out'],
  [/\bquiz\b/i, 'quiz'],
  [/\bbooks?\b|book (club|fair|launch|presentation)|library|reading|poetry/i, 'books'],
  [/\btalk\b|lecture|panel|in conversation|seminar/i, 'talk'],
  // wycieczka z przewodnikiem po souku to nie nocny targ z lampionami (Biennial guided walking tours, Souq Al Mina – tester A 27.11)
  [/guided (walking )?tours?|walking tours?/i, 'walking_tour'],
  [/night market|flea|bazaar|farmers'? market|winter market|christmas market|craft market|food market|urban market|souq|souk/i, 'market'],
  [/workshop|arts (and|&) crafts|craft/i, 'workshop'], // ogólne warsztaty – po tańcu, jodze itd.
  [/frieze|art fair|art week|art dubai|art abu dhabi|abu dhabi art|art exhibition|gallery|alserkal|jameel arts|421 arts|art foundation|art museum|tashkeel/i, 'artfair'],
  [/teamlab|immersive|digital art|museum|art gallery|biennial/i, 'museums'],
  // na końcu: bieg w parku archeologicznym to nadal bieg
  // fort/zamek ma własne zdjęcie (albo ikonkę) – nie uliczkę starego miasta z wieżą wiatrową
  [/\bfort\b|castle|(?<!dibba al )\bhisn\b|qasr al hosn/i, 'fort'],  // Dibba Al Hisn to miasto, nie fort
  // stanowisko archeologiczne / ruiny (Shimal, Pałac Królowej Saby) – nie zachowana uliczka z wieżą wiatrową (tester 26.11)
  [/archaeolog\w* (site|park)|\bruins\b|queen of sheba|\btombs?\b/i, 'ruins'],
  [/heritage village|heritage area|old village|pearling village|abandoned village|archaeolog|ruins|mud ?brick|historic (district|site|neighbourhood)|al fahidi|al bastakiya|heart of sharjah|qasr al hosn|(?<!dibba al )\bhisn\b/i, 'heritage'],
  // jedzenie i święta (event: brunch świąteczny, kolacja sylwestrowa) – przed plażą/farmą na końcu
  // koncert kolęd / świąteczne śpiewanie – scena z chórem, nie stół z indykiem (tester 26.11)
  // immersyjny spektakl („The Jury Experience: The Deadly Boat Ride”) to nie rejs łódką (tester A 27.11)
  [/jury experience|murder mystery|immersive (theat|show)/i, 'theatre'],
  // chór (One Day Choir 'Unwritten') – nie zespół rockowy (tester A 27.11)
  [/\bcarols?\b|\b(choir|choral)\b[\s\S]*\b(xmas|christmas|festive)\b|christmas (concert|sing|choir)|festive (concert|choir)|season of wonder/i, 'carols'],
  [/\bchoir\b|choral/i, 'choir'],  // chór bez świąt: własne zdjęcie albo ikonka
  [/new year|\bnye\b|hogmanay/i, 'nye'],
  [/santa|christmas|xmas|\bnatale\b|\bno[eë]l\b/i, 'xmas'],  // brunch z Mikołajem → zdjęcie świąteczne (zgłoszenie 26.11)
  [/\bbrunch\b(?! that burns)/i, 'brunch'],
  [/breakfast/i, 'breakfast'],
  [/dinner|buffet|\blunch\b|sunday roast|\broast\b|tasting menu|by the course|set menu|thanksgiving|turkey|iftar|suhoor/i, 'dinner'],
  [/christmas|xmas|santa|festive|\badvent\b|gingerbread/i, 'xmas'],
  [/\bexpo\b|trade (show|fair)|summit|conference|\bforum\b|(international|games|food|jewell?ery|perfumes?|watch|boat|motor|hunting)\b.*\b(exhibition|show)\b/i, 'expo'],
  [/concert|world tour/i, 'concert'],
  // na samym końcu, tylko gdy nic innego nie pasuje (koncert na plaży to koncert)
  // farma pereł i rejsy łodzią mają własne zdjęcia (albo ikonkę) – nie gaj palmowy
  [/pearl (farm|diving|journey)|\bpearls?\b.*\b(farm|tour|trip)/i, 'pearl'],
  [/\babra\b|\bdhow\b|boat (ride|trip|tour|cruise)|creek cruise|ferry/i, 'boat'],
  [/oasis/i, 'farm'],          // zdjęcie 'farm' to gaj palmowy z falajem = oaza
  [/\bfarm\b/i, 'cropfarm'],  // prawdziwa farma: szklarnie, grządki, zwierzęta
  [/al qudra|love lake/i, 'lakes'],
  // pustynia (wydmy) – też ośrodki na pustyni, np. Ritz-Carlton Al Wadi Desert (nie góry z 'wadi'; zgłoszenie 26.11)
  [/desert (safari|reserve|conservation|park|resort|camp|retreat)|al wadi desert|marmoom|sand ?dunes|dune bash|liwa(?!\))/i, 'desert'],
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
const NO_FALLBACK = new Set(['zipline', 'skydive', 'balloon', 'ropes', 'waxmuseum', 'lm_sharjah_mosque', 'lm_khalifa_mosque', 'lm_al_majaz', 'butterfly', 'crocodile', 'rainforest', 'immersive', 'santa', 'horseriding', 'ruins', 'carols', 'facepaint', 'sport_ladies', 'sailing', 'obstacle', 'bodybuilding', 'dance_ladies', 'afternoon_tea', 'fort', 'cropfarm', 'pearl', 'boat', 'mangrove', 'cinema_indoor', 'legoland', 'trampoline', 'lakes', 'rally', 'carshow', 'aquafit', 'painting', 'cooking', 'workshop', 'aquarium', 'zoo', 'waterpark', 'viewpoint', 'mosque', 'farm', 'bungee', 'flying', 'watersports', 'heritage', 'dance', 'snow', 'ice_rink', 'tennis', 'trail_mountain', 'walking_tour', 'choir']);

// Pojedyncze pliki z widokiem konkretnego miasta w ogólnej puli (running-2 ma Burj Khalifę): tylko dla tego miasta.
// (Sharjah Half Marathon i bieg w Abu Zabi dostawały panoramę Dubaju – tester 26.11)
const CITY_ONLY = new Map<number, string>([
  [PHOTO_FILES.running?.[1], 'Dubai'],  // running-2
].filter(([f]) => f != null) as [number, string][]);

// Zdjęcia o bardzo konkretnej treści w ogólnej puli kategorii (oferty biorą zdjęcie z puli typu oferty):
// tylko dla kart, których tytuł/miejsce do nich pasuje. Inaczej każda „night out” miała karaoke, każda kolacja
// – kuchnię indyjską albo teppanyaki, każdy day pass – basen wśród wydm (tester 27.11).
const ONLY_IF = new Map<string, RegExp>([
  ['mosque-1', /old|historic|heritage|al bidya|village|small|ancient|mud|al badiyah/i],
  // ludzie szkicujący rzeźbę: tylko zajęcia rysunku, nie wystawy (Spices and Wonders, zgłoszenie Agi 27.11)
  ['lm_louvre_in-3', /draw|sketch|art class|workshop|life drawing|atelier/i],
  // kontrola doboru zdjęć 27.11: zdjęcia z konkretną kuchnią / czynnością tylko dla pasujących kart
  ['night_out-1', /karaoke|open mic|live (music|band|dj)|\bdj\b|band|singer|gig|party|after ?dark|night shift|raise a mic/i],
  ['dinner-5', /arab|leban|mezze|emirati|turkish|shawarma|middle east|oriental|syrian|iftar|sultan|levant|majlis|persian|moroccan|dawat|journey to the orient/i],
  ['dinner-6', /italian|pizza|pasta|trattoria|tuscan|paparazzi|serata/i],
  ['lunch-5', /dim sum|chinese|cantonese|yum cha|asian|teahouse/i],
  ['dinner-3', /seafood|fish|crab|ceviche|lobster|oyster|prawn|surf (and|&) turf|beach/i],
  ['breakfast-6', /arab|emirati|leban|turkish|middle east|abra|majlis/i],
  ['zoo-1', /\bzoo\b|safari|wildlife park|emirates park/i],
  ['desert-2', /resort|camp|glamping|\bstay\b|ritz|retreat|lodge|hotel/i],
  ['lm_etihad_arena_in-2', /comedy|stand[- ]?up|comedian|talk|keynote|awards|smith/i],
  ['night_out-5', /karaoke/i],
  ['ladies_night-9', /karaoke|sing/i],  // panie śpiewają karaoke – nie przy ladies night z DJ-em (HUSHH, tester A 27.11)
  ['night_out-6', /shisha|hookah|arabic|lebanese|levant|majlis|turkish|moroccan|persian|emirati/i],
  ['dinner-7', /indian|biryani|curry|tandoor|desi|pakistani|dawat|punjabi|bhatia|masala|kerala|thali|nepal|sri lankan|mughal/i],
  ['dinner-8', /teppan|japanese|wagyu|hibachi|benihana|yakiniku|omakase|robata/i],
  ['day_pass-8', /desert|bab al shams|al maha|qasr al sarab|telal|mleiha|al wadi|liwa|dunes?\b/i],
  // tester B 27.11: świece Candlelight przy recitalu Yuja Wang; wydmy przy biegu na plaży Al Heera i w Ripe Market;
  // stół z indykiem przy zapalaniu choinki; kameralny klub z gitarą przy koncertach w arenie (Home Alone, Encanto) i festiwalu na plaży
  ['candlelight-5', /candlelight/i],
  ['running-3', /desert|dunes?\b|trail|qudra|wadi|mountain|ultra|sand/i],
  ['xmas-1', /brunch|dinner|lunch|feast|roast|turkey|buffet|menu|dining|supper|tea\b|meal|table|restaurant|grill|kitchen/i],
  ['xmas-2', /brunch|dinner|lunch|feast|roast|turkey|buffet|menu|dining|supper|tea\b|meal|table|restaurant|grill|kitchen/i],
  // Christmas Day w Turtle Bay Bar & Grill dostał jarmark świąteczny (zgłoszenie 27.11): jarmark tylko dla jarmarków,
  // choinka na dziedzińcu nie dla posiłków – kolacja/lunch/brunch świąteczny dostaje tylko stół (xmas-1, xmas-2)
  ['xmas-4', /market|bazaar|\bfair\b|village|souk|stalls?\b|winter wonderland/i],
  ['xmas-3', /^(?![\s\S]*(brunch|dinner|lunch|feast|roast|turkey|buffet|menu|dining|supper|tea\b|meal|restaurant|grill|kitchen|four[- ]course|set menu))/i],
  ['concert-5', /^(?![\s\S]*(arena|stadium|festival|beach|park\b|circuit|amphitheat|in concert|district|yasalam|after[- ]race|etihad (live|park)|harbour))/i],
  ['brunch-10', /asian|japanese|chinese|dim sum|sushi|zuma|thai|korean|vietnam|izakaya|yum cha|baikingu|cantonese|nobu|hakkasan|shanghai|noodle|ramen|sake|nikkei|peking|bao\b/i],
]);
// Zdjęcia z wieżowcami w ogólnej puli: tylko w miastach z wieżowcami (Ain Al Madhab Gardens w Fudżajrze dostawał park z wieżowcami – tester 27.11)
const TOWERS = new Set(['Dubai', 'Abu Dhabi', 'Sharjah']);
const SKYLINE_FILES = new Set(['parks-1', 'lunch-3', 'dinner-2', 'night_out-2']);
// Zdjęcia wyłączone (pliki zostają do decyzji właściciela): AI narysowało inny budynek niż prawdziwy
// – Etihad Arena ma pofalowaną, poziomo żłobkowaną fasadę, a nie kopułę ani „czaszę” (zgłoszenie 27.11.2026)
// przegląd 27.11 (Coca-Cola Arena-2 przywrócone: prawdziwa arena JEST okrągła z rombami – zdjęcie z Wikimedia); Opera ma kształt dhow, nie muszli;
// lm_saadiyat-4 i lm_yas-1 pokazują wymyślone budynki (na Yas – ta sama „czasza” co fałszywa Etihad Arena)
const DISABLED = new Set(['lm_etihad_arena-1', 'lm_etihad_arena-2', 'lm_dubai_opera-1', 'lm_saadiyat-4', 'lm_yas-1',
  // amfiteatr Khor Fakkan: AI dorysowało wodospad i inną bryłę (zgłoszenie Agi 27.11)
  'lm_khorfakkan_amph-1', 'lm_khorfakkan_amph-2',
  // Al Marjan Island: AI narysowało wyspy innego kształtu (zgłoszenie właściciela 27.11)
  'lm_marjan-1']);
const NIGHT = new Set(['dinner-1', 'dinner-2', 'dinner-9', 'night_out-1', 'night_out-3', 'night_out-4', 'ladies_night-5', 'happy_hour_dubai-1', 'lm_marina-1']);
function allowed(f: number, item: Item, text: string): boolean {
  const n = PHOTO_NAMES.get(f);
  if (!n) return true;
  if (DISABLED.has(n)) return false;
  // zdjęcie nocne przy wydarzeniu/ofercie w dzień (Sunday Roast od 12:30 z księżycem na zdjęciu – zgłoszenie Agi 27.11)
  if (NIGHT.has(n)) {
    const t = /(\d{1,2}):\d{2}/.exec(item.whenFull ?? item.when ?? '');
    if (t && Number(t[1]) >= 6 && Number(t[1]) < 16) return false;
  }
  // panorama jednego miasta też na ścieżce rodzaju z tytułu (Saturday Run – Khorfakkan Beach dostawał Burj Khalifę – tester A 27.11)
  const only = CITY_ONLY.get(f);
  if (only && only !== item.city) return false;
  const re = ONLY_IF.get(n);
  if (re && !re.test(text) && !(item.catKey === 'food' && (n === 'xmas-1' || n === 'xmas-2'))) return false;
  if (SKYLINE_FILES.has(n) && !TOWERS.has(item.city)) return false;
  // świąteczny event z kategorii jedzenie (Christmas Day at Nikki Beach): stół, nie choinka ani jarmark (tester A 27.11)
  if ((n === 'xmas-3' || n === 'xmas-4') && item.catKey === 'food') return false;
  return true;
}

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
  // zdjęcia Corniche i Wielkiego Meczetu to Abu Dhabi – „Ajman Corniche” czy meczet Szejka Zajeda w Fudżajrze ich nie dostają
  if (lm && (lm[1] === 'lm_corniche' || lm[1] === 'lm_grand_mosque') && item.city !== 'Abu Dhabi') lm = undefined;
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
  // Afternoon tea (bywało oznaczone jako staycation/lunch): własne zdjęcie, a do czasu jego zrobienia ikonka (zgłoszenie 26.11.2026)
  if (/afternoon tea|high tea|le go[uû]ter/i.test(item.rawTitle ?? item.title)) return [...(PHOTO_FILES.afternoon_tea ?? [])];
  // Staycation w hotelu przy plaży („Beach Resort”, Al Aqah, Fujairah): zdjęcie resortu z basenem i plażą (day pass),
  // a nie pokój – zgłoszenie testerki 26.11.2026 (Fairmont Fujairah Beach Resort).
  if (item.kind === 'deal' && item.catKey === 'staycation' && /beach (resort|hotel|club)|resort (&|and) spa|al aqah|beachfront/i.test(placeText) && PHOTO_FILES.day_pass) {
    return [...PHOTO_FILES.day_pass];
  }
  // Oferty (ladies night, brunch, quiz) w znanym miejscu: zdjęcie rodzaju oferty. Budynek tylko dla staycation / day pass.
  if (lm && item.kind === 'deal' && item.catKey !== 'staycation' && item.catKey !== 'day_pass' && CAT[item.catKey]) lm = undefined;
  // Areny i sale (Etihad Arena, Coca-Cola Arena, Opera...): event z rozpoznanym rodzajem (komedia, koncert DJ, teatr)
  // dostaje zdjęcie rodzaju, a zdjęcie budynku tylko gdy rodzaju nie widać – żeby wieczór w arenie nie miał 5 takich samych kart.
  // Rodzaj z tytułu wygrywa ze znanym miejscem (Kayaking at Louvre -> kajaki, Swan Lake w Operze -> teatr).
  // (nazwę samego miejsca wycinamy z tytułu, żeby "Museum of the Future" nie stało się zwykłym "museum")
  const rest = lm ? (item.rawTitle ?? item.title).replace(new RegExp(lm[0].source, 'gi'), ' ') : (item.rawTitle ?? item.title);
  // góry Jais: rodzaj z tytułu (park linowy, taras) NIE wygrywa – to zawsze góry, nie hala wspinaczkowa (wyjątek: sylwester, koncert, festiwal)
  const typeHit0 = item.kind !== 'deal' && lm ? RULES.find(([re]) => re.test(rest)) : undefined;
  // (bez biegu: „festival running from 11 to 31 December” to nie bieg – Winter City, tester A 27.11)
  // event w sali/arenie bez rodzaju w tytule: rodzaj z opisu („Cycles – Boy Blue”: „Nine hip hop dancers…” → taniec, nie kampus NYU; zgłoszenie 27.11)
  const typeHitD = !typeHit0 && item.kind === 'event' && lm && VENUES.has(lm[1]) && item.description
    ? RULES.find(([re, k]) => PHOTO_FILES[k] && k !== 'running' && re.test(item.description!.replace(new RegExp(lm![0].source, 'gi'), ' '))) : undefined;
  const typeHit = lm && lm[1] === 'lm_jebel_jais' && typeHit0 && !/^(nye|fireworks|concert|festival)/.test(typeHit0[1]) ? undefined : (typeHit0 ?? typeHitD);
  // świąteczny koncert w arenie (Mariah Carey's Christmastime w Etihad Arena): wnętrze areny, nie stół z indykiem (tester B 27.11)
  if (typeHit && lm && VENUES.has(lm[1]) && /^(xmas|carols)$/.test(typeHit[1]) && PHOTO_FILES[`${lm[1]}_in`]) return [...PHOTO_FILES[`${lm[1]}_in`]];
  if (typeHit && PHOTO_FILES[typeHit[1]]) return [...PHOTO_FILES[typeHit[1]]];
  // koncert w muzeum / w parku Expo City (Dhafer Youssef w Luwrze, Wasla Festival w Jubilee Park): scena koncertowa,
  // nie sala z rzeźbami ani kopuła Al Wasl (tester A 27.11)
  if (lm && item.kind === 'event' && item.catKey === 'music' && PHOTO_FILES.concert
    && (lm[1] === 'lm_louvre' || lm[1] === 'lm_museum_future' || (lm[1] === 'lm_expo_city' && !/al wasl/i.test(placeText)))) return [...PHOTO_FILES.concert];
  // event w arenie bez rozpoznanego rodzaju: wnętrze tej areny (lm_<arena>_in) + jej zdjęcia z zewnątrz
  if (lm && item.kind === 'event' && VENUES.has(lm[1])) {
    // mecz / walka w arenie (koszykówka, boks, darts): nie wnętrze z koncertu (kontrola zdjęć 27.11)
    if (item.catKey === 'sport') return [];
    // tylko wnętrze, gdy jest: zdjęcia budynku z zewnątrz robione przez AI nie wyglądają jak prawdziwy budynek (Etihad Arena, zgłoszenie 27.11)
    const inside = PHOTO_FILES[`${lm[1]}_in`] ?? [];
    return inside.length ? [...inside] : [...(PHOTO_FILES[lm[1]] ?? [])];
  }
  if (lm) return [...(PHOTO_FILES[lm[1]] ?? []), ...(VENUES.has(lm[1]) ? PHOTO_FILES[`${lm[1]}_in`] ?? [] : [])]; // znane miejsce bez zdjęcia: ikonka, nie obce zdjęcie
  // oferta, której tytuł mówi o czymś innym niż bar/kolacja (Saturday Run Club, Wellness Morning, Pasta Masterclass, Quiz): zdjęcie tej czynności (kontrola zdjęć 27.11)
  if (item.kind === 'deal') {
    const t = item.rawTitle ?? item.title;
    const k = /run club|\bparkrun\b|\bcommunity run\b/i.test(t) ? 'running' : /yoga|pilates|wellness morning|sound ?bath|meditation/i.test(t) ? 'yoga'
      : /masterclass|cooking class|workshop|decorating|mixology class/i.test(t) ? 'classes' : /\bquiz\b|\bbingo\b/i.test(t) ? 'quiz'
      : /trampoline|flip (out|junior)|bounce/i.test(t) ? 'trampoline'
      : item.catKey === 'night_out' && /steak|sushi|bbq|barbecue|wings|pizza|taco|burger|moules|seafood|crab|tapas|pasta|curry|ramen|noodle|roast|tomahawk|brisket|slider|gyoza|grill night|theme night|buffet/i.test(t) ? 'dinner' : undefined;
    if (k && PHOTO_FILES[k]) return [...PHOTO_FILES[k]];
  }
  if (item.kind !== 'deal' || !item.catKey || item.catKey === 'other') {
    const hit = RULES.find(([re]) => re.test((item.rawTitle ?? item.title)));
    if (hit && PHOTO_FILES[hit[1]]) keys = [hit[1]];
    else if (hit && NO_FALLBACK.has(hit[1])) return [];
  }
  // Event bez rozpoznanego rodzaju z tytułu: ikonka zamiast ogólnego zdjęcia kategorii (to ono dawało złe zdjęcia).
  // wyjątek: event muzyczny bez rodzaju dostaje ogólne zdjęcie sceny koncertowej (gdy już jest)
  // stand-up bez słowa „comedy” w tytule (Sergey Orlov, „Fe Eid Amina”): rodzaj z opisu, nie scena koncertowa (tester A 27.11)
  if (!keys && item.kind === 'event' && PHOTO_FILES.comedy && /^(music|comedy|nightlife)$/.test(item.catKey ?? '')
    && /\b(comedy|stand[- ]?up|comedian)\b/i.test(item.description ?? '') && !/\bplay\b|theat(re|er)/i.test(item.description ?? '')) keys = ['comedy'];
  if (!keys && item.kind === 'event') {
    if (item.catKey === 'music' && PHOTO_FILES.concert) keys = ['concert'];
    else return [];
  }
  if (!keys) keys = CAT[item.catKey] ?? [];
  const zones = SKYLINE_ZONES[item.city];
  const suf = zones === null || (zones && item.zone && zones.has(item.zone)) ? CITY_SUFFIX[item.city] : undefined;
  const out: number[] = [];
  for (const k of keys) {
    out.push(...(PHOTO_FILES[k] ?? []).filter((f) => !(CITY_ONLY.get(f) && CITY_ONLY.get(f) !== item.city)));
    if (suf) out.push(...(PHOTO_FILES[`${k}_${suf}`] ?? []));
  }
  return out;
}

/** Zdjęcie dla karty albo null (wtedy karta pokazuje ikonkę). `avoid` = zdjęcie poprzedniej karty. */
export function photoFor(item: Item, avoid?: number | null): number | null {
  const row: any = item.event ?? item.deal ?? item.place;
  if (row?.id && PHOTO_OFF.has(String(row.id))) return null;
  const text = `${item.rawTitle ?? item.title} ${item.where ?? ''} ${item.event?.venue ?? ''}`;
  const p = pool(item).filter((f) => allowed(f, item, text));
  if (!p.length) return null;
  let i = hash(item.key) % p.length;
  if (p.length > 1 && p[i] === avoid) i = (i + 1) % p.length;
  return p[i];
}
