import { getLLMText, source } from '@/lib/source';
import { notFound } from 'next/navigation';

type RouteParams = {
  slug?: string[];
};

export const revalidate = false;

export async function GET(
  _req: Request,
  { params }: { params: Promise<RouteParams> },
) {
  const resolved = await params;
  const page = source.getPage(resolved.slug?.slice(0, -1));
  if (!page) notFound();

  return new Response(await getLLMText(page), {
    headers: {
      'Content-Type': 'text/markdown',
    },
  });
}

export function generateStaticParams() {
  return source.getPages().map((page) => ({
    slug: [...page.slugs, 'index.mdx'],
  }));
}
