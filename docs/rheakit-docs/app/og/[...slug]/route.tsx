import { getPageImage, source } from '@/lib/source';
import { notFound } from 'next/navigation';
import { ImageResponse } from 'next/og';
import { generate as DefaultImage } from 'fumadocs-ui/og';

type RouteParams = {
  slug: string[];
};

export const revalidate = false;

export async function GET(
  _req: Request,
  { params }: { params: Promise<RouteParams> },
) {
  const resolved = await params;
  const page = source.getPage(resolved.slug.slice(0, -1));
  if (!page) notFound();

  return new ImageResponse(
    <DefaultImage
      title={page.data.title}
      description={page.data.description}
      site="RheaKit Docs"
    />,
    {
      width: 1200,
      height: 630,
    },
  );
}

export function generateStaticParams() {
  return source.getPages().map((page) => ({
    slug: getPageImage(page).segments,
  }));
}
