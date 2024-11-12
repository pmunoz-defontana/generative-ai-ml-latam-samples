// MIT No Attribution
//
// Copyright 2024 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import { Outlet } from "react-router-dom";
import { NavBar } from "@/components/ui/navbar";
import { ChartAreaIcon } from "lucide-react";
import { Toaster } from "@/components/ui/toaster";

interface HeaderGradientProps {
  colors: string[];
}

export const HeaderGradient: React.FC<HeaderGradientProps> = ({ colors }) => {
  const gradientString = `linear-gradient(to right, ${colors.join(", ")})`;

  return (
    <div className="absolute inset-0 -z-10 mx-0 max-w-none overflow-hidden">
      <div className="absolute left-1/2 top-0 ml-[-38rem] h-[25rem] w-[81.25rem] dark:[mask-image:linear-gradient(white,transparent)]">
        <div
          className="absolute inset-0 [mask-image:radial-gradient(farthest-side_at_top,white,transparent)]"
          style={{ background: gradientString }}
        ></div>
        <svg
          viewBox="0 0 1113 440"
          aria-hidden="true"
          className="absolute left-1/2 top-0 ml-[-19rem] w-[69.5625rem] fill-white blur-[30px] dark:hidden"
        >
          <path d="M.016 439.5s-9.5-300 434-300S882.516 20 882.516 20V0h230.004v439.5H.016Z"></path>
        </svg>
      </div>
    </div>
  );
};

export default function Root() {
  return (
    <>
      <NavBar icon={<ChartAreaIcon className="h-5 w-5 sm:h-6 sm:w-6" />} />
      <HeaderGradient colors={["#B4F8A7", "#A6A6F0", "#BFA8EF"]} />
      <main className="container mx-auto mt-4">
        <Outlet />
        <Toaster />
      </main>
    </>
  );
}
