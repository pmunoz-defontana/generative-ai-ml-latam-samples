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

import { Amplify } from "aws-amplify";
import { Authenticator } from "@aws-amplify/ui-react";
import React from "react";
import ReactDOM from "react-dom/client";
import {
  Route,
  RouterProvider,
  createBrowserRouter,
  createRoutesFromElements,
} from "react-router-dom";

import "./index.css";

import Error from "@/routes/Errors";
import List from "@/routes/List";
import Root from "@/routes/Root";
import { Logout } from "@/routes/Logout";
import { RequireAuth } from "@/routes/RequireAuth";
import { Login } from "@/routes/Login";
import { listLoader } from "@/loaders/list";
import { fetchAuthSession } from "aws-amplify/auth";

import "@/lib/i18n";

const env = import.meta.env; // Vite environment variables

Amplify.configure(
  {
    Auth: {
      Cognito: {
        userPoolId: env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: env.VITE_COGNITO_USER_POOL_CLIENT_ID,
        identityPoolId: env.VITE_COGNITO_IDENTITY_POOL_ID,
      },
    },
    API: {
      REST: {
        Backend: {
          endpoint: env.VITE_API_GATEWAY_REST_API_ENDPOINT,
          region: env.VITE_AWS_REGION,
        },
      },
    },
  },
  {
    API: {
      REST: {
        headers: async () => {
          return {
            Authorization: `Bearer ${(await fetchAuthSession()).tokens?.idToken?.toString()}`,
          };
        },
      },
    },
  },
);

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route errorElement={<Error />}>
      <Route
        element={
          <RequireAuth>
            <Root />
          </RequireAuth>
        }
      >
        <Route index element={<List />} loader={listLoader} />
      </Route>
      <Route path="login" element={<Login />} />
      <Route path="logout" element={<Logout />} />
    </Route>,
  ),
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Authenticator.Provider>
      <RouterProvider router={router} />
    </Authenticator.Provider>
  </React.StrictMode>,
);
