"use client";

import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      position="top-right"
      className="toaster group"
      toastOptions={{
        style: {
          background: "white",
          color: "#1f2937",
          border: "1px solid #e5e7eb",
          boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
          zIndex: 9999,
        },
      }}
      style={{
        zIndex: 9999,
      }}
      {...props}
    />
  );
};

export { Toaster };
