import { useAuth } from "@/_core/hooks/useAuth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger, useSidebar } from "@/components/ui/sidebar";
import { startLogin } from "@/const";
import { useIsMobile } from "@/hooks/useMobile";
import { BriefcaseBusiness, Cable, FileCheck2, LayoutDashboard, LogOut, PanelLeft, UsersRound } from "lucide-react";
import { CSSProperties, useEffect, useRef, useState } from "react";
import { useLocation } from "wouter";
import { DashboardLayoutSkeleton } from "./DashboardLayoutSkeleton";

const menuItems = [
  { icon: LayoutDashboard, label: "Visão geral", path: "/" },
  { icon: UsersRound, label: "Perfis", path: "/perfis" },
  { icon: BriefcaseBusiness, label: "Oportunidades", path: "/oportunidades" },
  { icon: FileCheck2, label: "Candidaturas", path: "/candidaturas" },
  { icon: Cable, label: "Integrações", path: "/integracoes" },
];
const SIDEBAR_WIDTH_KEY = "findwork-sidebar-width";
const DEFAULT_WIDTH = 278;
const MIN_WIDTH = 212;
const MAX_WIDTH = 384;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarWidth, setSidebarWidth] = useState(() => Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || DEFAULT_WIDTH);
  const { loading, user } = useAuth();
  useEffect(() => localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth)), [sidebarWidth]);
  if (loading) return <DashboardLayoutSkeleton />;
  if (!user) return <div className="min-h-screen bg-[#f6f4ef] p-6 flex items-center justify-center"><div className="max-w-md text-center rounded-[2rem] bg-white p-10 shadow-[0_30px_80px_rgba(20,45,37,0.12)]"><p className="text-xs font-bold uppercase tracking-[0.22em] text-[#bf7d2d]">FindWork</p><h1 className="mt-4 font-[var(--font-display)] text-4xl text-[#16332b]">Seu próximo passo, com critério.</h1><p className="mt-4 text-sm leading-6 text-[#66766f]">Acesse para manter perfis, oportunidades e candidaturas organizados em um espaço privado.</p><Button onClick={() => startLogin()} className="mt-8 w-full bg-[#163f35] hover:bg-[#0c2e26]">Acessar espaço privado</Button></div></div>;
  return <SidebarProvider style={{ "--sidebar-width": `${sidebarWidth}px` } as CSSProperties}><LayoutContent setSidebarWidth={setSidebarWidth}>{children}</LayoutContent></SidebarProvider>;
}

function LayoutContent({ children, setSidebarWidth }: { children: React.ReactNode; setSidebarWidth: (width: number) => void }) {
  const { user, logout } = useAuth();
  const [location, setLocation] = useLocation();
  const { state, toggleSidebar } = useSidebar();
  const isCollapsed = state === "collapsed";
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();
  const activeMenuItem = menuItems.find(item => item.path === location);
  useEffect(() => {
    const move = (event: MouseEvent) => { if (!isResizing) return; const left = sidebarRef.current?.getBoundingClientRect().left ?? 0; const width = event.clientX - left; if (width >= MIN_WIDTH && width <= MAX_WIDTH) setSidebarWidth(width); };
    const up = () => setIsResizing(false);
    if (isResizing) { document.addEventListener("mousemove", move); document.addEventListener("mouseup", up); document.body.style.cursor = "col-resize"; document.body.style.userSelect = "none"; }
    return () => { document.removeEventListener("mousemove", move); document.removeEventListener("mouseup", up); document.body.style.cursor = ""; document.body.style.userSelect = ""; };
  }, [isResizing, setSidebarWidth]);
  return <><div className="relative" ref={sidebarRef}><Sidebar collapsible="icon" className="border-0 bg-[#12382f] text-white" disableTransition={isResizing}><SidebarHeader className="h-[94px] p-5"><div className="flex items-center gap-3"><button onClick={toggleSidebar} className="grid h-9 w-9 place-items-center rounded-xl text-[#d7e4dd] hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#e1ab5b]" aria-label="Alternar navegação"><PanelLeft className="h-4 w-4" /></button>{!isCollapsed && <div className="min-w-0"><p className="font-[var(--font-display)] text-xl leading-none tracking-tight">FindWork</p><p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.17em] text-[#b5c8bf]">Copiloto de carreira</p></div>}</div></SidebarHeader><SidebarContent><div className="px-4 pb-3 group-data-[collapsible=icon]:hidden"><p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#9fb7ac]">Workspace privado</p></div><SidebarMenu className="px-3">{menuItems.map(item => <SidebarMenuItem key={item.path}><SidebarMenuButton isActive={location === item.path} onClick={() => setLocation(item.path)} tooltip={item.label} className="h-11 rounded-xl px-3 text-[#dce9e2] hover:bg-white/10 hover:text-white data-[active=true]:bg-[#e8b96d] data-[active=true]:text-[#19362d]"><item.icon className="h-4 w-4" /><span className="font-medium">{item.label}</span></SidebarMenuButton></SidebarMenuItem>)}</SidebarMenu></SidebarContent><SidebarFooter className="p-4"><DropdownMenu><DropdownMenuTrigger asChild><button className="flex w-full items-center gap-3 rounded-xl p-2 text-left hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#e1ab5b]"><Avatar className="h-9 w-9 border border-white/15"><AvatarFallback className="bg-[#254f44] text-xs text-white">{user?.name?.slice(0, 1).toUpperCase() || "U"}</AvatarFallback></Avatar><div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden"><p className="truncate text-sm font-medium text-white">{user?.name || "Seu espaço"}</p><p className="mt-0.5 truncate text-xs text-[#aec2b7]">{user?.email || "Conta protegida"}</p></div></button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-48"><DropdownMenuItem onClick={logout} className="cursor-pointer text-destructive focus:text-destructive"><LogOut className="mr-2 h-4 w-4" />Sair com segurança</DropdownMenuItem></DropdownMenuContent></DropdownMenu></SidebarFooter></Sidebar><div className={`absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-[#e8b96d]/70 ${isCollapsed ? "hidden" : ""}`} onMouseDown={() => setIsResizing(true)} /></div><SidebarInset className="bg-[#f6f4ef]">{isMobile && <div className="sticky top-0 z-40 flex h-14 items-center gap-2 border-b border-[#dfe6df] bg-[#f6f4ef]/95 px-3 backdrop-blur"><SidebarTrigger className="h-9 w-9 rounded-lg bg-white" /><span className="text-sm font-semibold text-[#17362c]">{activeMenuItem?.label || "FindWork"}</span></div>}<main className="min-h-screen px-4 py-6 sm:px-7 lg:px-10 lg:py-9">{children}</main></SidebarInset></>;
}
