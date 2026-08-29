import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { trpc } from "@/lib/trpc";
import { FileText, PencilLine, Plus, Upload, X } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { toast } from "sonner";

type ProfileForm = { id?: number; label: string; professionalArea: string; targetRole: string; seniority: string; summary: string; skills: string; regions: string; workModes: string; resumeText: string; isPrimary: boolean };
const blank: ProfileForm = { label: "", professionalArea: "", targetRole: "", seniority: "", summary: "", skills: "", regions: "", workModes: "Remoto", resumeText: "", isPrimary: false };
const parseList = (value: string) => value.split(",").map(item => item.trim()).filter(Boolean);

export default function ProfilesPage() {
  const utils = trpc.useUtils();
  const { data: profiles, isLoading } = trpc.career.profiles.list.useQuery();
  const [form, setForm] = useState<ProfileForm>(blank);
  const [editing, setEditing] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const uploadResume = trpc.career.profiles.uploadResume.useMutation({
    onSuccess: async () => { await utils.career.dashboard.invalidate(); toast.success("Documento-fonte armazenado com segurança."); },
    onError: error => toast.error(error.message),
  });
  const save = trpc.career.profiles.save.useMutation({
    onSuccess: async profile => {
      await utils.career.profiles.list.invalidate();
      await utils.career.dashboard.invalidate();
      if (pendingFile && profile?.id) {
        const contentBase64 = await fileToBase64(pendingFile);
        await uploadResume.mutateAsync({
          profileId: profile.id,
          fileName: pendingFile.name,
          mimeType: pendingFile.type === "text/markdown" || pendingFile.name.endsWith(".md") ? "text/markdown" : "text/plain",
          contentBase64,
        });
      }
      toast.success("Perfil salvo com segurança.");
      setPendingFile(null);
      setForm(blank);
      setEditing(false);
    },
    onError: error => toast.error(error.message),
  });
  const update = (field: keyof ProfileForm, value: string | boolean) => setForm(current => ({ ...current, [field]: value }));
  const startEdit = (profile: NonNullable<typeof profiles>[number]) => {
    setForm({ id: profile.id, label: profile.label, professionalArea: profile.professionalArea, targetRole: profile.targetRole, seniority: profile.seniority, summary: profile.summary, skills: profile.skills.join(", "), regions: profile.regions.join(", "), workModes: profile.workModes.join(", "), resumeText: profile.resumeText, isPrimary: profile.isPrimary });
    setPendingFile(null);
    setEditing(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const readTextFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!/\.(txt|md)$/i.test(file.name)) { toast.error("Por enquanto, importe arquivos .txt ou .md, ou cole o texto do currículo."); return; }
    const reader = new FileReader();
    reader.onload = () => { update("resumeText", String(reader.result ?? "")); setPendingFile(file); toast.message("Arquivo preparado para armazenamento seguro ao salvar o perfil."); };
    reader.readAsText(file);
  };
  const submit = () => save.mutate({ id: form.id, label: form.label, professionalArea: form.professionalArea, targetRole: form.targetRole, seniority: form.seniority, summary: form.summary, skills: parseList(form.skills), regions: parseList(form.regions), workModes: parseList(form.workModes), resumeText: form.resumeText, isPrimary: form.isPrimary });
  const reset = () => { setForm(blank); setEditing(false); setPendingFile(null); };
  return <div className="mx-auto max-w-7xl space-y-7"><PageHeading eyebrow="Perfis independentes" title="Cada carreira com seu próprio contexto." text="Mantenha trajetórias, preferências, competências e currículos separados. As recomendações e os rascunhos sempre respeitam o perfil selecionado." /><div className="grid gap-6 xl:grid-cols-[0.92fr_1.3fr]"><Card className="h-fit border-0 bg-[#143d33] text-white shadow-[0_20px_50px_rgba(20,58,47,0.18)]"><CardContent className="p-6"><div className="flex items-center justify-between"><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#b8d0c4]">Seus perfis</p><Badge className="bg-[#e7b367] text-[#18372e] hover:bg-[#e7b367]">{profiles?.length ?? 0}</Badge></div><div className="mt-5 space-y-3">{isLoading ? <p className="text-sm text-[#c4d7cd]">Carregando perfis…</p> : profiles?.length ? profiles.map(profile => <button key={profile.id} onClick={() => startEdit(profile)} className="w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:bg-white/10"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{profile.label}</p><p className="mt-1 text-xs text-[#bcd0c6]">{profile.targetRole}</p></div>{profile.isPrimary && <span className="rounded-full bg-[#e7b367] px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-[#143d33]">Principal</span>}</div><p className="mt-3 text-xs text-[#d6e3dc]">{profile.professionalArea} · {profile.seniority}</p></button>) : <div className="rounded-2xl border border-dashed border-white/20 p-4 text-sm leading-6 text-[#c3d5cb]">Nenhum perfil ainda. Crie o primeiro para começar a orientar as oportunidades.</div>}</div><Button onClick={() => { setForm(blank); setEditing(true); }} variant="outline" className="mt-5 w-full border-white/25 bg-transparent text-white hover:bg-white/10 hover:text-white"><Plus className="mr-2 h-4 w-4" />Novo perfil</Button></CardContent></Card><Card className="border-0 bg-white shadow-[0_12px_35px_rgba(21,54,43,0.06)]"><CardContent className="p-6 sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#bb7b2d]">{form.id ? "Edição protegida" : "Novo perfil"}</p><h2 className="mt-1 font-[var(--font-display)] text-3xl text-[#18362d]">{form.id ? `Atualizar ${form.label || "perfil"}` : "Quem você quer representar?"}</h2></div>{editing && <Button variant="ghost" size="icon" onClick={reset} aria-label="Cancelar edição"><X className="h-4 w-4" /></Button>}</div><div className="mt-7 grid gap-5 md:grid-cols-2"><Field label="Nome do perfil"><Input value={form.label} onChange={event => update("label", event.target.value)} placeholder="Ex.: Carreira em tecnologia" /></Field><Field label="Área profissional"><Input value={form.professionalArea} onChange={event => update("professionalArea", event.target.value)} placeholder="Ex.: Tecnologia" /></Field><Field label="Cargo ou direção-alvo"><Input value={form.targetRole} onChange={event => update("targetRole", event.target.value)} placeholder="Ex.: Tech Lead" /></Field><Field label="Senioridade"><Input value={form.seniority} onChange={event => update("seniority", event.target.value)} placeholder="Ex.: Sênior" /></Field><Field label="Competências (separadas por vírgula)"><Input value={form.skills} onChange={event => update("skills", event.target.value)} placeholder="Liderança, JavaScript, Cloud" /></Field><Field label="Regiões de interesse"><Input value={form.regions} onChange={event => update("regions", event.target.value)} placeholder="São Paulo, Remoto Brasil" /></Field><Field label="Modalidades desejadas" className="md:col-span-2"><Input value={form.workModes} onChange={event => update("workModes", event.target.value)} placeholder="Remoto, Híbrido" /></Field><Field label="Resumo profissional" className="md:col-span-2"><Textarea value={form.summary} onChange={event => update("summary", event.target.value)} rows={4} placeholder="Síntese da trajetória, escopo e objetivos profissionais…" /></Field><div className="md:col-span-2"><div className="flex items-center justify-between gap-3"><Label htmlFor="resumeText">Currículo-fonte</Label><label className="inline-flex items-center gap-2 text-xs font-semibold text-[#27604e] hover:text-[#17483a]"><Upload className="h-3.5 w-3.5" />Importar texto<input type="file" accept=".txt,.md,text/plain,text/markdown" className="sr-only" onChange={readTextFile} /></label></div><p className="mt-1 text-xs leading-5 text-[#79887f]">Cole o texto ou importe um arquivo .txt/.md. A adaptação usará apenas essas informações e não criará experiências.</p><Textarea id="resumeText" value={form.resumeText} onChange={event => update("resumeText", event.target.value)} rows={12} className="mt-3 font-mono text-xs leading-5" placeholder="Cole aqui o conteúdo completo e revisado do currículo…" /></div><div className="flex items-center gap-3 md:col-span-2"><Switch id="primary" checked={form.isPrimary} onCheckedChange={checked => update("isPrimary", checked)} /><Label htmlFor="primary" className="text-sm font-normal text-[#52675c]">Usar como perfil principal neste espaço</Label></div></div><div className="mt-7 flex flex-wrap gap-3"><Button onClick={submit} disabled={save.isPending || uploadResume.isPending} className="bg-[#163f35] hover:bg-[#0c2e26]"><FileText className="mr-2 h-4 w-4" />{save.isPending || uploadResume.isPending ? "Salvando…" : "Salvar perfil"}</Button>{form.id && <Button variant="outline" onClick={reset}><PencilLine className="mr-2 h-4 w-4" />Cancelar edição</Button>}</div></CardContent></Card></div></div>;
}

export function PageHeading({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) { return <section className="max-w-3xl"><p className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7782d]">{eyebrow}</p><h1 className="mt-2 font-[var(--font-display)] text-4xl tracking-tight text-[#18362d] sm:text-5xl">{title}</h1><p className="mt-4 text-sm leading-6 text-[#687a70]">{text}</p></section>; }
function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) { return <div className={className}><Label>{label}</Label><div className="mt-2">{children}</div></div>; }
function fileToBase64(file: File) { return new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => { const result = String(reader.result ?? ""); resolve(result.split(",")[1] ?? ""); }; reader.onerror = () => reject(new Error("Não foi possível preparar o arquivo do currículo.")); reader.readAsDataURL(file); }); }
