import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import DashboardLayout from "@/components/DashboardLayout";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import ApplicationsPage from "./pages/ApplicationsPage";
import DashboardPage from "./pages/DashboardPage";
import IntegrationsPage from "./pages/IntegrationsPage";
import OpportunitiesPage from "./pages/OpportunitiesPage";
import ProfilesPage from "./pages/ProfilesPage";
import { Route, Switch } from "wouter";

function Router() {
  return <DashboardLayout><Switch><Route path="/" component={DashboardPage} /><Route path="/perfis" component={ProfilesPage} /><Route path="/oportunidades" component={OpportunitiesPage} /><Route path="/candidaturas" component={ApplicationsPage} /><Route path="/integracoes" component={IntegrationsPage} /><Route><DashboardPage /></Route></Switch></DashboardLayout>;
}

export default function App() {
  return <ErrorBoundary><ThemeProvider defaultTheme="light"><TooltipProvider><Toaster richColors position="top-right" /><Router /></TooltipProvider></ThemeProvider></ErrorBoundary>;
}
