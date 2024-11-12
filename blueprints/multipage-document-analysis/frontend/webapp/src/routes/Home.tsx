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

import { useLoaderData, Await } from "react-router-dom";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";

type ItemsData = {
  items: Record<string, string>[];
};

export default function Home() {
  const loaderData = useLoaderData() as ItemsData;

  return (
    <Suspense fallback={<Skeleton />}>
      <Await resolve={loaderData.items} errorElement={<p>Error</p>}>
        {(loadedData) => (
          <div>
            <p>This is a sample rendering with items fetched from an API:</p>
            <pre className="whitespace-pre-wrap rounded-md border border-orange-400 bg-orange-100 p-2 text-xs text-orange-950">
              {JSON.stringify(loadedData, null, 2)}
            </pre>
          </div>
        )}
      </Await>
    </Suspense>
  );
}
