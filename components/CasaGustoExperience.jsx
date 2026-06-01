"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const dishes = [
  {
    name: "Seafood Pasta al Limone",
    description: "Handmade tagliolini folded with Amalfi lemon, saffron shellfish jus, and a delicate finish of bottarga.",
    ingredients: "Tagliolini, langoustine, clams, saffron, Amalfi lemon",
    chef: "Pair with Vermentino for a luminous coastal finish.",
    image: "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=1400&q=85",
  },
  {
    name: "Grilled Octopus Affumicato",
    description: "Ember-kissed octopus with smoked potato crema, Castelvetrano olive, fennel pollen, and herb oil.",
    ingredients: "Mediterranean octopus, potato, olives, fennel, basil oil",
    chef: "Our most cinematic antipasto for two guests to share.",
    image: "https://images.unsplash.com/photo-1625944230945-1b7dd3b949ab?auto=format&fit=crop&w=1400&q=85",
  },
  {
    name: "Italian Burrata Giardino",
    description: "Silken burrata with heirloom tomato petals, aged balsamic pearls, basil blossoms, and toasted focaccia crumb.",
    ingredients: "Puglian burrata, tomato, balsamic, basil, focaccia",
    chef: "Begin the evening here for a graceful expression of Italy.",
    image: "https://images.unsplash.com/photo-1608897013039-887f21d8c804?auto=format&fit=crop&w=1400&q=85",
  },
];

const gallery = [
  "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1506368249639-73a05d6f6488?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=900&q=85",
];

const testimonials = [
  "A dinner that felt private, cinematic, and deeply Italian.",
  "The pasta course alone deserves a journey across the city.",
  "Warm service, immaculate wine pairings, and unforgettable atmosphere.",
  "Casa Gusto turns a reservation into a romantic occasion.",
];

function Reveal({ children, className = "" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 46 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-90px" }}
      transition={{ duration: 0.95, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default function CasaGustoExperience() {
  const pageRef = useRef(null);
  const [reserved, setReserved] = useState(false);
  const { scrollYProgress } = useScroll();
  const heroY = useTransform(scrollYProgress, [0, 0.22], [0, 190]);

  useEffect(() => {
    const context = gsap.context(() => {
      gsap.utils.toArray(".gsap-reveal").forEach((element) => {
        gsap.fromTo(
          element,
          { autoAlpha: 0, y: 64 },
          {
            autoAlpha: 1,
            y: 0,
            duration: 1.15,
            ease: "power3.out",
            scrollTrigger: { trigger: element, start: "top 82%" },
          },
        );
      });

      gsap.utils.toArray(".parallax-card").forEach((element) => {
        gsap.to(element, {
          yPercent: -10,
          ease: "none",
          scrollTrigger: { trigger: element, scrub: 1.2 },
        });
      });
    }, pageRef);

    return () => context.revert();
  }, []);

  function submitReservation(event) {
    event.preventDefault();
    setReserved(true);
  }

  return (
    <main ref={pageRef} className="overflow-hidden bg-nero text-ivory">
      <section className="relative min-h-screen overflow-hidden">
        <motion.div style={{ y: heroY }} className="absolute inset-0 slow-zoom parallax-fill">
          <Image
            src="https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=2400&q=90"
            alt="Chef plating an elegant Italian fine dining dish"
            fill
            priority
            sizes="100vw"
            className="object-cover"
          />
        </motion.div>
        <div className="absolute inset-0 hero-gradient" />
        <nav className="luxury-container relative z-10 flex items-center justify-between py-8 text-xs uppercase tracking-[0.36em] text-ivory/80">
          <span className="font-serif text-2xl tracking-[0.22em] text-ivory">CG</span>
          <div className="hidden gap-8 md:flex">
            <a href="#menu" className="transition hover:text-champagne">Menu</a>
            <a href="#wine" className="transition hover:text-champagne">Wine</a>
            <a href="#reserve" className="transition hover:text-champagne">Reserve</a>
          </div>
        </nav>
        <div className="luxury-container relative z-10 flex min-h-[78vh] items-center justify-center text-center">
          <motion.div initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.18 } } }}>
            <motion.p variants={{ hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } }} className="eyebrow mb-7">Luxury Italian Fine Dining</motion.p>
            <motion.h1 variants={{ hidden: { opacity: 0, y: 34 }, show: { opacity: 1, y: 0 } }} className="display-title">CASA GUSTO</motion.h1>
            <motion.p variants={{ hidden: { opacity: 0, y: 26 }, show: { opacity: 1, y: 0 } }} className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-ivory/82 sm:text-xl">
              Authentic Italian Gastronomy. A culinary journey inspired by the traditions of Italy.
            </motion.p>
            <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="mt-11 flex flex-col justify-center gap-4 sm:flex-row">
              <a href="#reserve" className="rounded-full bg-champagne px-8 py-4 text-sm font-semibold uppercase tracking-[0.22em] text-nero shadow-gold transition duration-500 hover:scale-105 hover:bg-ivory">Reserve a Table</a>
              <a href="#menu" className="rounded-full border border-ivory/30 px-8 py-4 text-sm font-semibold uppercase tracking-[0.22em] text-ivory transition duration-500 hover:border-champagne hover:text-champagne">Explore Menu</a>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section id="menu" className="bg-ivory py-24 text-nero sm:py-32">
        <div className="luxury-container">
          <Reveal className="mx-auto max-w-3xl text-center">
            <p className="eyebrow">Signature Dishes</p>
            <h2 className="section-title mt-4">Artisanal plates composed with quiet drama.</h2>
          </Reveal>
          <div className="mt-20 space-y-24">
            {dishes.map((dish, index) => (
              <article key={dish.name} className={`grid items-center gap-10 lg:grid-cols-2 ${index % 2 ? "lg:[&>div:first-child]:order-2" : ""}`}>
                <div className="parallax-card group relative h-[460px] overflow-hidden rounded-t-full shadow-luxury image-veil">
                  <Image src={dish.image} alt={dish.name} fill sizes="(min-width: 1024px) 50vw, 100vw" className="object-cover transition duration-1000 group-hover:scale-110" />
                </div>
                <Reveal className="gsap-reveal">
                  <p className="eyebrow">0{index + 1} / Chef Selection</p>
                  <h3 className="mt-5 font-serif text-5xl leading-none tracking-[-0.03em] text-forest">{dish.name}</h3>
                  <p className="mt-6 text-lg leading-8 text-nero/70">{dish.description}</p>
                  <div className="mt-8 grid gap-5 border-y border-forest/15 py-7 sm:grid-cols-2">
                    <div><span className="text-xs uppercase tracking-[0.3em] text-sage">Ingredients</span><p className="mt-2 text-sm leading-6">{dish.ingredients}</p></div>
                    <div><span className="text-xs uppercase tracking-[0.3em] text-sage">Chef Recommends</span><p className="mt-2 text-sm leading-6">{dish.chef}</p></div>
                  </div>
                </Reveal>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-nero py-24 sm:py-32">
        <div className="luxury-container">
          <Reveal className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
            <div><p className="eyebrow">Visual Food Gallery</p><h2 className="section-title mt-4 max-w-3xl">Editorial photography for evenings worth remembering.</h2></div>
            <p className="max-w-sm text-sm leading-7 text-ivory/60">A fashion-inspired masonry rhythm with warm plates, soft shadows, and refined motion.</p>
          </Reveal>
          <div className="mt-14 columns-1 gap-5 sm:columns-2 lg:columns-3">
            {gallery.map((src, index) => (
              <div key={src} className="group mb-5 break-inside-avoid overflow-hidden rounded-[2rem] bg-white/5 shadow-luxury">
                <Image src={src} alt={`Casa Gusto gallery moment ${index + 1}`} width={900} height={index % 2 ? 1180 : 760} className="h-auto w-full object-cover transition duration-1000 group-hover:scale-105 group-hover:brightness-110" />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-forest bg-linen-texture py-24 sm:py-32">
        <div className="luxury-container grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <Reveal><p className="eyebrow">The Story of Casa Gusto</p><h2 className="section-title mt-4">Tradition, restraint, and the romance of the Italian table.</h2></Reveal>
          <Reveal className="glass-card rounded-[2rem] p-8 sm:p-12">
            <p className="text-lg leading-9 text-ivory/78">Casa Gusto was created as an intimate stage for contemporary Italian gastronomy: handmade pasta prepared daily, vegetables chosen for peak season, seafood handled with precision, and service choreographed to feel personal rather than performative.</p>
            <div className="gold-line my-8" />
            <p className="leading-8 text-ivory/64">Every visit moves from aperitivo to dessert with cinematic pacing, warm candlelight, subtle gold details, and a team devoted to making each guest feel expected.</p>
          </Reveal>
        </div>
      </section>

      <section id="wine" className="relative bg-nero py-24 sm:py-32">
        <div className="luxury-container grid gap-12 lg:grid-cols-2 lg:items-center">
          <Reveal>
            <p className="eyebrow">Wine Experience</p>
            <h2 className="section-title mt-4">Rare Italian bottles, glass reflections, and pairings with intention.</h2>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {["Barolo Riserva", "Etna Bianco", "Brunello", "Amarone"].map((wine) => <div key={wine} className="glass-card rounded-3xl p-6 transition duration-500 hover:border-champagne/50 hover:bg-champagne/10"><p className="font-serif text-2xl">{wine}</p><p className="mt-3 text-sm leading-6 text-ivory/58">Curated for depth, aroma, and a graceful finish.</p></div>)}
            </div>
          </Reveal>
          <Reveal className="relative mx-auto h-[560px] w-full max-w-md">
            <div className="absolute inset-x-10 bottom-6 h-28 rounded-full wine-glow blur-3xl" />
            <Image src="https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=1100&q=85" alt="Premium Italian wine bottle and glasses" fill sizes="(min-width: 1024px) 45vw, 100vw" className="rounded-t-full object-cover shadow-luxury" />
          </Reveal>
        </div>
      </section>

      <section className="bg-ivory py-24 text-nero sm:py-32">
        <div className="luxury-container grid gap-12 lg:grid-cols-2 lg:items-center">
          <Reveal className="relative h-[560px] overflow-hidden rounded-[3rem] shadow-luxury"><Image src="https://images.unsplash.com/photo-1577219491135-ce391730fb2c?auto=format&fit=crop&w=1200&q=85" alt="Casa Gusto executive chef portrait" fill sizes="(min-width: 1024px) 50vw, 100vw" className="object-cover" /></Reveal>
          <Reveal>
            <p className="eyebrow">Chef Experience</p>
            <h2 className="section-title mt-4 text-forest">“Luxury is the confidence to let exceptional ingredients speak softly.”</h2>
            <p className="mt-8 text-lg leading-8 text-nero/68">Our chef’s philosophy is rooted in regional Italian memory, contemporary precision, and an obsession with texture, temperature, and timing.</p>
          </Reveal>
        </div>
      </section>

      <section className="bg-wood py-20">
        <div className="overflow-hidden">
          <div className="marquee-track flex w-max gap-5">
            {[...testimonials, ...testimonials].map((quote, index) => <div key={`${quote}-${index}`} className="glass-card w-[360px] rounded-[2rem] p-7"><p className="text-champagne">★★★★★</p><p className="mt-5 font-serif text-2xl leading-8">{quote}</p><p className="mt-6 text-xs uppercase tracking-[0.3em] text-ivory/45">Google Reviews</p></div>)}
          </div>
        </div>
      </section>

      <section id="reserve" className="relative py-24 sm:py-32">
        <Image src="https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=2200&q=85" alt="Casa Gusto restaurant interior at night" fill sizes="100vw" className="-z-10 object-cover" />
        <div className="absolute inset-0 -z-10 bg-black/72" />
        <div className="luxury-container grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
          <Reveal><p className="eyebrow">Reservations</p><h2 className="section-title mt-4">Reserve a table for an evening of Italian ceremony.</h2><p className="mt-7 max-w-md leading-8 text-ivory/65">For anniversaries, candlelit dinners, private celebrations, and guests who want every detail handled beautifully.</p></Reveal>
          <Reveal>
            <form onSubmit={submitReservation} className="glass-card grid gap-5 rounded-[2rem] p-6 sm:grid-cols-2 sm:p-10">
              {["Name", "Email", "Phone", "Guests", "Date", "Time"].map((field) => <label key={field} className="text-xs uppercase tracking-[0.26em] text-ivory/58">{field}<input required type={field === "Email" ? "email" : field === "Date" ? "date" : field === "Time" ? "time" : field === "Guests" ? "number" : "text"} min={field === "Guests" ? 1 : undefined} className="mt-3 w-full rounded-full border-white/10 bg-black/35 px-5 py-4 text-base normal-case tracking-normal text-ivory outline-none transition focus:border-champagne focus:ring-champagne" /></label>)}
              <button className="rounded-full bg-champagne px-8 py-4 text-sm font-bold uppercase tracking-[0.24em] text-nero transition duration-500 hover:scale-[1.02] hover:bg-ivory sm:col-span-2">Confirm Reservation</button>
              {reserved && <p className="rounded-2xl border border-champagne/40 bg-champagne/10 p-4 text-center text-sm text-champagne sm:col-span-2">Your request has been received. Casa Gusto will confirm your table shortly.</p>}
            </form>
          </Reveal>
        </div>
      </section>

      <footer className="bg-nero py-14">
        <div className="luxury-container">
          <div className="gold-line mb-10" />
          <div className="grid gap-10 md:grid-cols-4">
            <div><p className="font-serif text-4xl">Casa Gusto</p><p className="mt-4 text-sm leading-7 text-ivory/55">Authentic Italian gastronomy for refined evenings.</p></div>
            <div><p className="eyebrow">Social</p><p className="mt-4 text-ivory/65">Instagram · WhatsApp</p></div>
            <div><p className="eyebrow">Location</p><p className="mt-4 text-ivory/65">Via Roma 18, Italian Quarter</p></div>
            <div><p className="eyebrow">Hours</p><p className="mt-4 text-ivory/65">Tue–Sun · 18:00–23:30<br />Reservations essential</p></div>
          </div>
        </div>
      </footer>
    </main>
  );
}
