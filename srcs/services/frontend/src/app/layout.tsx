import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ML Salary Prediction",
  description: "Predict salary with an ML model"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
