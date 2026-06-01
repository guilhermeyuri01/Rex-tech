import "./globals.css";

export const metadata = {
  title: "Casa Gusto | Authentic Italian Fine Dining",
  description:
    "Casa Gusto is an ultra-premium Italian fine dining restaurant for handmade pasta, curated wines, romantic dinners, and Michelin-inspired hospitality.",
  keywords: [
    "Casa Gusto",
    "Italian fine dining",
    "luxury restaurant",
    "Michelin inspired restaurant",
    "handmade pasta",
    "wine experience",
  ],
  openGraph: {
    title: "Casa Gusto | Authentic Italian Gastronomy",
    description: "A cinematic Italian fine dining experience shaped by premium ingredients, artisanal cuisine, and elegant service.",
    type: "website",
    images: [
      {
        url: "https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=1600&q=85",
        width: 1600,
        height: 1067,
        alt: "Casa Gusto Italian fine dining presentation",
      },
    ],
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
