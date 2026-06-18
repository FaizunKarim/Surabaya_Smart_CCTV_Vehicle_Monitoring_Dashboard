import type { Metadata } from "next";
import { Bricolage_Grotesque, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import "leaflet/dist/leaflet.css";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Surabaya Smart CCTV Vehicle Monitoring Dashboard",
  description:
    "Dashboard monitoring CCTV publik Surabaya dengan peta live, daftar CCTV, stream HLS, dan analitik kendaraan real-time.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="id"
      className={`${bricolage.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
