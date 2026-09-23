export type Role = 'admin' | 'editor' | 'moderator';
export type Kind = 'page' | 'service' | 'project' | 'settings' | 'article' | 'campaign';
export type BlockType = 'bento' | 'projects' | 'process' | 'text' | 'faq' | 'contact' | 'features' | 'media' | 'stats' | 'quote' | 'logos' | 'pricing' | 'gallery' | 'divider' | 'news' | 'advert' | 'spotlight' | 'tabs' | 'timeline' | 'comparison';
export interface BlockItem {title:string;text:string;value?:string;link_label?:string;link_url?:string;image?:string;art?:string}
export interface Block { id: string; type: BlockType; enabled: boolean; eyebrow: string; title: string; text: string; items: BlockItem[]; theme?:string;spacing?:string;width?:string;animation?:string;columns?:number;align?:string;image?:string;art?:string;link_label?:string;link_url?:string;category?:string;limit?:number;campaign?:string }
export interface ContentData {
  title: string; slug: string; description: string; order: number;
  art?: string; body?: string; tags?: string[]; image?: string;
  author?:string;published_on?:string;featured?:boolean;sponsor?:string;link_url?:string;link_label?:string;starts_on?:string;ends_on?:string;analytics_enabled?:boolean;news_in_navigation?:boolean;
  category?: string; client?: string; year?: string; demo?: boolean;
  in_navigation?: boolean; navigation_label?: string; blocks?: Block[]; brand?: string; tagline?: string; accent?: string; design?: string; email?: string; location?: string;motion?:string;intro?:string;
}
export interface RecordItem {
  id: string; kind: Kind; data: ContentData; live: ContentData | null; state: 'draft'|'pending'|'published'|'rejected';
  block_count?:number;revision: number; updated_at: number; note: string;
}
export interface User { id: number; name: string; email: string; role: Role; csrf: string; active?: number }
export interface Media { id: string; filename: string; alt: string; width: number; height: number }
export interface Revision { revision: number; action: string; created_at: number; name: string|null }
export interface Inquiry { id: string; name: string; email: string; service: string; message: string; status: string; created_at: number }
export interface Overview { published: number; drafts: number; pending: number; new_inquiries: number; recent: RecordItem[] }

export interface ModuleSpec{type:BlockType;name:string;category:string;description:string;keywords:string;supports:string[];defaults:Block}
export interface PageTemplate{id:string;name:string;description:string;blocks:Block[]}
export interface Asset{id:string;name:string;category:string;url:string}
export interface Catalog{version:number;modules:ModuleSpec[];templates:PageTemplate[];assets:Asset[];limits:{blocks:number;items:number;presets:number}}
export interface Preset{id:string;name:string;block:Block;created_by:number;created_at?:number}
