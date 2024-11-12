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

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Link, useNavigate } from "react-router-dom";
import {
  LogOut,
  MoonIcon,
  SunIcon,
  Globe,
  Check,
  AppWindowIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthenticator } from "@aws-amplify/ui-react";
import Logo from "@/assets/aws.svg";
import { useTranslation } from "react-i18next";

interface NavBarProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
}

function NavBar({ className, icon, ...props }: NavBarProps) {
  const [darkMode, setDarkMode] = useState(false);
  const { t, i18n } = useTranslation();

  const {
    user: { username },
  } = useAuthenticator((context) => [context.user]);

  const navigate = useNavigate();

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-4 shadow-sm md:px-6",
        className,
      )}
      {...props}
    >
      <Link to="/" className="flex w-8 justify-center sm:w-10 md:block">
        <img src={Logo} alt="AWS" />
      </Link>
      <Link
        to="/"
        className="flex items-center gap-1 text-lg font-bold md:gap-2"
      >
        {icon || <AppWindowIcon className="h-5 w-5 sm:h-6 sm:w-6" />}
        <span className="text-xs sm:text-sm md:text-base">{t("appName")}</span>
      </Link>
      <div className="flex items-center gap-2 md:gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <Globe className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-48" align="end">
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => i18n.changeLanguage("en")}
            >
              <span className="flex w-full items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <span>🇺🇸</span>
                  <span>{t("languageSelector.en")}</span>
                </span>
                {i18n.language === "en" && <Check className="h-4 w-4" />}
              </span>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => i18n.changeLanguage("es")}
            >
              <span className="flex w-full items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <span>🇪🇸</span>
                  <span>{t("languageSelector.es")}</span>
                </span>
                {i18n.language === "es" && <Check className="h-4 w-4" />}
              </span>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => i18n.changeLanguage("pt")}
            >
              <span className="flex w-full items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <span>🇧🇷</span>
                  <span>{t("languageSelector.pt")}</span>
                </span>
                {i18n.language === "pt" && <Check className="h-4 w-4" />}
              </span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="icon"
          className="hidden" // sm:block" TODO: make the switch work
          onClick={() => setDarkMode((prev) => !prev)}
        >
          {darkMode ? (
            <SunIcon className="h-5 w-5" />
          ) : (
            <MoonIcon className="h-5 w-5" />
          )}
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Avatar className="h-8 w-8 cursor-pointer sm:h-10 sm:w-10">
              <AvatarImage src={`https://github.com/${username}.png`} />
              <AvatarFallback>
                {username.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end">
            <DropdownMenuLabel>
              {t("mainNav.loggedInAs", { username: username })}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => navigate("/logout")}
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>{t("mainNav.logout")}</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export { NavBar };
