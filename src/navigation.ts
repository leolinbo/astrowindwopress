import { getPermalink, getBlogPermalink, getAsset } from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Products',
      links: [
        {
          text: 'Track Lighting',
          href: getPermalink('/products/track-lighting'),
        },
        {
          text: 'LED Downlights',
          href: getPermalink('/products/led-downlights'),
        },
        {
          text: 'Magnetic Track Lights',
          href: getPermalink('/products/magnetic-track-lights'),
        },
        {
          text: 'Commercial Lighting',
          href: getPermalink('/products/commercial-lighting'),
        },
      ],
    },
    {
      text: 'OEM / ODM',
      href: getPermalink('/oem-odm'),
    },
    {
      text: 'About Us',
      links: [
        {
          text: 'Our Factory',
          href: getPermalink('/about'),
        },
        {
          text: 'Quality Control',
          href: getPermalink('/quality-control'),
        },
        {
          text: 'Certifications',
          href: getPermalink('/certifications'),
        },
      ],
    },
    {
      text: 'Blog',
      href: getBlogPermalink(),
    },
    {
      text: 'Contact',
      href: getPermalink('/contact'),
    },
  ],
  actions: [
    {
      text: 'Get Quote',
      href: getPermalink('/contact'),
      variant: 'primary',
    },
  ],
};

export const footerData = {
  links: [
    {
      title: 'Products',
      links: [
        { text: 'Track Lighting', href: getPermalink('/products/track-lighting') },
        { text: 'LED Downlights', href: getPermalink('/products/led-downlights') },
        { text: 'Magnetic Track Lights', href: getPermalink('/products/magnetic-track-lights') },
        { text: 'Commercial Lighting', href: getPermalink('/products/commercial-lighting') },
      ],
    },
    {
      title: 'Services',
      links: [
        { text: 'OEM / ODM Manufacturing', href: getPermalink('/oem-odm') },
        { text: 'Custom Lighting Solutions', href: getPermalink('/oem-odm') },
        { text: 'Wholesale & Bulk Orders', href: getPermalink('/contact') },
      ],
    },
    {
      title: 'Company',
      links: [
        { text: 'About ENCORE', href: getPermalink('/about') },
        { text: 'Our Factory', href: getPermalink('/about') },
        { text: 'Quality Control', href: getPermalink('/quality-control') },
        { text: 'Certifications', href: getPermalink('/certifications') },
        { text: 'Blog', href: getBlogPermalink() },
      ],
    },
    {
      title: 'Support',
      links: [
        { text: 'Contact Us', href: getPermalink('/contact') },
        { text: 'FAQ', href: getPermalink('/faq') },
        { text: 'Privacy Policy', href: getPermalink('/privacy') },
        { text: 'Terms', href: getPermalink('/terms') },
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Terms', href: getPermalink('/terms') },
    { text: 'Privacy Policy', href: getPermalink('/privacy') },
  ],
  socialLinks: [
    { ariaLabel: 'LinkedIn', icon: 'tabler:brand-linkedin', href: 'https://www.linkedin.com/company/37545158/' },
    { ariaLabel: 'Facebook', icon: 'tabler:brand-facebook', href: 'https://www.facebook.com/EncoreCommericalLighting' },
    { ariaLabel: 'Instagram', icon: 'tabler:brand-instagram', href: 'https://www.instagram.com/encoreledcommerciallighting/' },
    { ariaLabel: 'YouTube', icon: 'tabler:brand-youtube', href: 'https://www.youtube.com/@encorecommerciallighting4413' },
    { ariaLabel: 'RSS', icon: 'tabler:rss', href: getAsset('/rss.xml') },
  ],
  footNote: `
    <strong>HK HQ:</strong> Room 1, 16/F, Empress Plaza 17-19 Chatham Road South Tsim Sha Tsui, KL.<br>
    <strong>Factory:</strong> 2/F, Bldg 8th, Zhengzhong Industrial Park, Qiaotou Community, Fuyong, Bao'an Dist, Shenzhen.<br>
    <strong>Tel:</strong> +852 6768 2519 &nbsp;|&nbsp; <strong>Email:</strong> <a href="mailto:sales@encore-tech.com">sales@encore-tech.com</a><br>
    &copy; 2026 Encore International Co., Ltd. All rights reserved.
  `,
};
