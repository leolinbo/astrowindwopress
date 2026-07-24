import type { PaginateFunction } from 'astro';
import type { Post, Taxonomy, MetaData } from '~/types';
import { APP_BLOG } from 'astrowind:config';
import { cleanSlug, trimSlash, BLOG_BASE, POST_PERMALINK_PATTERN, CATEGORY_BASE, TAG_BASE } from './permalinks';

// ---------------------------------------------------------------------------
// WordPress REST API types
// ---------------------------------------------------------------------------

interface WpTitle {
  rendered: string;
}

interface WpContent {
  rendered: string;
}

interface WpRendered {
  rendered: string;
}

interface WpMediaSize {
  source_url: string;
  width: number;
  height: number;
}

interface WpMediaDetails {
  sizes: Record<string, WpMediaSize>;
}

interface WpFeaturedMedia {
  source_url: string;
  media_details: WpMediaDetails;
  alt_text: string;
}

interface WpTerm {
  taxonomy: 'category' | 'post_tag';
  slug: string;
  name: string;
}

interface WpAuthor {
  name: string;
}

interface WpEmbedded {
  'wp:term'?: WpTerm[][];
  'wp:featuredmedia'?: WpFeaturedMedia[];
  author?: WpAuthor[];
}

interface WpPost {
  id: number;
  slug: string;
  date: string;
  modified: string;
  title: WpTitle;
  content: WpContent;
  excerpt: WpRendered;
  _embedded?: WpEmbedded;
}

// ---------------------------------------------------------------------------
// WordPress REST API — replace with your own WordPress site URL
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// WordPress REST API — configure via environment variable or change here
// ---------------------------------------------------------------------------
// Set the WP_API_URL env var to your WordPress site's REST API root, e.g.:
//   WP_API_URL=https://example.com/wp-json/wp/v2 npm run dev
// If unset, the default URL below is used as a working demo.
// ---------------------------------------------------------------------------
const WP_API_BASE: string =
  import.meta.env.WP_API_URL ?? 'https://whitesmoke-jellyfish-711069.hostingersite.com/wp-json/wp/v2';

/**
 * Fetch all posts from WordPress, including embedded resources (categories,
 * tags, featured media, author) so we can build full Post objects.
 */
async function fetchWpPosts(): Promise<WpPost[]> {
  const url = `${WP_API_BASE}/posts?_embed&per_page=100`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`WordPress API error: ${res.status} ${res.statusText}`);
  return res.json();
}

/**
 * Estimate reading time from plain text (rough: 200 words/min).
 */
function estimateReadingTime(html: string): number {
  const text = html.replace(/<[^>]*>/g, '').trim();
  const words = text.split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.ceil(words / 200));
}

/**
 * Strip HTML tags from a string, returning clean text.
 */
function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim();
}

/**
 * Normalise a raw WordPress REST API post into our internal Post shape.
 */
function normalizeWpPost(raw: WpPost): Post {
  const embed = raw._embedded;

  // ---- category -----------------------------------------------------------
  const terms = (embed?.['wp:term'] ?? []).flat();
  const catTerm = terms.find((t) => t.taxonomy === 'category');
  const category: Taxonomy | undefined = catTerm
    ? { slug: cleanSlug(catTerm.slug), title: catTerm.name }
    : undefined;

  // ---- tags ---------------------------------------------------------------
  const tagTerms = terms.filter((t) => t.taxonomy === 'post_tag');
  const tags: Taxonomy[] = tagTerms.map((t) => ({
    slug: cleanSlug(t.slug),
    title: t.name,
  }));

  // ---- featured image -----------------------------------------------------
  const media = (embed?.['wp:featuredmedia'] ?? [])[0];
  let image: string | undefined;
  if (media) {
    const sizes = media.media_details?.sizes ?? {};
    // Pick medium_large first, then medium, then full, then source_url
    image =
      sizes.medium_large?.source_url ??
      sizes.medium?.source_url ??
      sizes.full?.source_url ??
      media.source_url ??
      undefined;
  }

  // ---- author -------------------------------------------------------------
  const authorData = (embed?.['author'] ?? [])[0];
  const author = authorData?.name ?? undefined;

  const slug = cleanSlug(raw.slug);
  const publishDate = new Date(raw.date);
  const updateDate = raw.modified ? new Date(raw.modified) : undefined;

  // Build permalink from the same pattern used by local posts
  const permalink = POST_PERMALINK_PATTERN.replace('%slug%', slug)
    .replace('%id%', String(raw.id))
    .replace('%category%', category?.slug ?? '')
    .replace('%year%', String(publishDate.getFullYear()).padStart(4, '0'))
    .replace('%month%', String(publishDate.getMonth() + 1).padStart(2, '0'))
    .replace('%day%', String(publishDate.getDate()).padStart(2, '0'))
    .replace('%hour%', String(publishDate.getHours()).padStart(2, '0'))
    .replace('%minute%', String(publishDate.getMinutes()).padStart(2, '0'))
    .replace('%second%', String(publishDate.getSeconds()).padStart(2, '0'));

  const cleanPermalink = permalink
    .split('/')
    .map((el) => trimSlash(el))
    .filter((el) => !!el)
    .join('/');

  return {
    id: String(raw.id),
    slug,
    permalink: cleanPermalink,

    publishDate,
    updateDate,

    title: stripHtml(raw.title?.rendered ?? ''),
    excerpt: stripHtml(raw.excerpt?.rendered ?? ''),
    image,

    category,
    tags,
    author,

    draft: false,

    metadata: {
      title: stripHtml(raw.title?.rendered ?? ''),
      description: stripHtml(raw.excerpt?.rendered ?? ''),
    } as MetaData,

    Content: raw.content?.rendered ?? '',

    readingTime: estimateReadingTime(raw.content?.rendered ?? ''),
  };
}

// ---------------------------------------------------------------------------
// Caching layer (kept identical to the original pattern)
// ---------------------------------------------------------------------------
let _posts: Array<Post>;

const load = async (): Promise<Array<Post>> => {
  const rawPosts = await fetchWpPosts();
  const normalized = rawPosts
    .map(normalizeWpPost)
    .sort((a, b) => b.publishDate.valueOf() - a.publishDate.valueOf())
    .filter((post) => !post.draft);
  return normalized;
};

// ---------------------------------------------------------------------------
// Exports — same API as the original so all pages continue working
// ---------------------------------------------------------------------------

/** */
export const isBlogEnabled = APP_BLOG.isEnabled;
export const isRelatedPostsEnabled = APP_BLOG.isRelatedPostsEnabled;
export const isBlogListRouteEnabled = APP_BLOG.list.isEnabled;
export const isBlogPostRouteEnabled = APP_BLOG.post.isEnabled;
export const isBlogCategoryRouteEnabled = APP_BLOG.category.isEnabled;
export const isBlogTagRouteEnabled = APP_BLOG.tag.isEnabled;

export const blogListRobots = APP_BLOG.list.robots;
export const blogPostRobots = APP_BLOG.post.robots;
export const blogCategoryRobots = APP_BLOG.category.robots;
export const blogTagRobots = APP_BLOG.tag.robots;

export const blogPostsPerPage = APP_BLOG?.postsPerPage;

/** */
export const fetchPosts = async (): Promise<Array<Post>> => {
  if (!_posts) {
    _posts = await load();
  }
  return _posts;
};

/** */
export const findPostsBySlugs = async (slugs: Array<string>): Promise<Array<Post>> => {
  if (!Array.isArray(slugs)) return [];

  const posts = await fetchPosts();

  return slugs.reduce(function (r: Array<Post>, slug: string) {
    posts.some(function (post: Post) {
      return slug === post.slug && r.push(post);
    });
    return r;
  }, []);
};

/** */
export const findPostsByIds = async (ids: Array<string>): Promise<Array<Post>> => {
  if (!Array.isArray(ids)) return [];

  const posts = await fetchPosts();

  return ids.reduce(function (r: Array<Post>, id: string) {
    posts.some(function (post: Post) {
      return id === post.id && r.push(post);
    });
    return r;
  }, []);
};

/** */
export const findLatestPosts = async ({ count }: { count?: number }): Promise<Array<Post>> => {
  const _count = count || 4;
  const posts = await fetchPosts();

  return posts ? posts.slice(0, _count) : [];
};

/** */
export const getStaticPathsBlogList = async ({ paginate }: { paginate: PaginateFunction }) => {
  if (!isBlogEnabled || !isBlogListRouteEnabled) return [];
  return paginate(await fetchPosts(), {
    params: { blog: BLOG_BASE || undefined },
    pageSize: blogPostsPerPage,
  });
};

/** */
export const getStaticPathsBlogPost = async () => {
  if (!isBlogEnabled || !isBlogPostRouteEnabled) return [];
  return (await fetchPosts()).flatMap((post) => ({
    params: {
      blog: post.permalink,
    },
    props: { post },
  }));
};

/** */
export const getStaticPathsBlogCategory = async ({ paginate }: { paginate: PaginateFunction }) => {
  if (!isBlogEnabled || !isBlogCategoryRouteEnabled) return [];

  const posts = await fetchPosts();
  const categories: Record<string, Taxonomy> = {};
  posts.map((post) => {
    if (post.category?.slug) {
      categories[post.category.slug] = post.category;
    }
  });

  return Array.from(Object.keys(categories)).flatMap((categorySlug) =>
    paginate(
      posts.filter((post) => post.category?.slug && categorySlug === post.category?.slug),
      {
        params: { category: categorySlug, blog: CATEGORY_BASE || undefined },
        pageSize: blogPostsPerPage,
        props: { category: categories[categorySlug] },
      }
    )
  );
};

/** */
export const getStaticPathsBlogTag = async ({ paginate }: { paginate: PaginateFunction }) => {
  if (!isBlogEnabled || !isBlogTagRouteEnabled) return [];

  const posts = await fetchPosts();
  const tags: Record<string, Taxonomy> = {};
  posts.map((post) => {
    if (Array.isArray(post.tags)) {
      post.tags.map((tag) => {
        tags[tag.slug] = tag;
      });
    }
  });

  return Array.from(Object.keys(tags)).flatMap((tagSlug) =>
    paginate(
      posts.filter((post) => Array.isArray(post.tags) && post.tags.find((elem) => elem.slug === tagSlug)),
      {
        params: { tag: tagSlug, blog: TAG_BASE || undefined },
        pageSize: blogPostsPerPage,
        props: { tag: tags[tagSlug] },
      }
    )
  );
};

/** */
export async function getRelatedPosts(originalPost: Post, maxResults: number = 4): Promise<Post[]> {
  const allPosts = await fetchPosts();
  const originalTagsSet = new Set(originalPost.tags ? originalPost.tags.map((tag) => tag.slug) : []);

  const postsWithScores = allPosts.reduce((acc: { post: Post; score: number }[], iteratedPost: Post) => {
    if (iteratedPost.slug === originalPost.slug) return acc;

    let score = 0;
    if (iteratedPost.category && originalPost.category && iteratedPost.category.slug === originalPost.category.slug) {
      score += 5;
    }

    if (iteratedPost.tags) {
      iteratedPost.tags.forEach((tag) => {
        if (originalTagsSet.has(tag.slug)) {
          score += 1;
        }
      });
    }

    acc.push({ post: iteratedPost, score });
    return acc;
  }, []);

  postsWithScores.sort((a, b) => b.score - a.score);

  const selectedPosts: Post[] = [];
  let i = 0;
  while (selectedPosts.length < maxResults && i < postsWithScores.length) {
    selectedPosts.push(postsWithScores[i].post);
    i++;
  }

  return selectedPosts;
}
