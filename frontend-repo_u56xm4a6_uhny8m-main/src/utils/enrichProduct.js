/** Match product titles/categories to the original Unsplash hero images. */
const IMAGES = {
  earbud: 'https://images.unsplash.com/photo-1518443895914-06e0f2eeaad6?q=80&w=1200&auto=format&fit=crop',
  vacuum: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=1200&auto=format&fit=crop',
  lamp: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=1200&auto=format&fit=crop',
  travel: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop',
  gaming: 'https://images.unsplash.com/photo-1587202372775-e229f172b9a7?q=80&w=1200&auto=format&fit=crop',
  monitor: 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?q=80&w=1200&auto=format&fit=crop',
  chair: 'https://images.unsplash.com/photo-1580480057503-bf9a8a6f0b08?q=80&w=1200&auto=format&fit=crop',
  webcam: 'https://images.unsplash.com/photo-1587825140708-5e5c9d16c699?q=80&w=1200&auto=format&fit=crop',
  skincare: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1200&auto=format&fit=crop',
  default: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1200&auto=format&fit=crop',
}

function pickImage(title = '', category = '') {
  const t = `${title} ${category}`.toLowerCase()
  if (/earbud|headphone|audio|sound/.test(t)) return IMAGES.earbud
  if (/vacuum|clean|hepa|quiet/.test(t)) return IMAGES.vacuum
  if (/lamp|light|desk light/.test(t)) return IMAGES.lamp
  if (/travel|kit|tsa/.test(t)) return IMAGES.travel
  if (/monitor|display|144hz|screen/.test(t)) return IMAGES.monitor
  if (/chair|ergonomic|office seat/.test(t)) return IMAGES.chair
  if (/webcam|camera/.test(t)) return IMAGES.webcam
  if (/gaming|gpu|pc|desktop|ibuypower|ryzen/.test(t)) return IMAGES.gaming
  if (/skincare|cleanser|moisturizer|cerave/.test(t)) return IMAGES.skincare
  return IMAGES.default
}

function inferCategory(title = '', category = '') {
  if (category && category !== 'Top picks' && category !== 'Your picks' && category !== 'Primary Item') {
    return category
  }
  const t = title.toLowerCase()
  if (/earbud|headphone/.test(t)) return 'Audio'
  if (/vacuum/.test(t)) return 'Home'
  if (/lamp/.test(t)) return 'Office'
  if (/monitor/.test(t)) return 'Monitors'
  if (/gaming|pc|desktop/.test(t)) return 'Gaming'
  if (/travel/.test(t)) return 'Travel'
  if (/chair/.test(t)) return 'Office'
  return category || 'General'
}

export function enrichProduct(product) {
  if (!product) return product
  const title =
    typeof product.title === 'string' && product.title.length > 80
      ? `${product.title.slice(0, 77)}…`
      : product.title || 'Product'
  const category = inferCategory(title, product.category || '')
  const hasGoodImage =
    product.image &&
    !product.image.includes('1523275335684') &&
    product.image.startsWith('http')

  return {
    ...product,
    title,
    category,
    price: Number(product.price) || 0,
    rating: Number(product.rating) || 4.5,
    image: hasGoodImage ? product.image : pickImage(title, category),
    specs: Array.isArray(product.specs) ? product.specs.slice(0, 4) : [],
    retailers: Array.isArray(product.retailers) ? product.retailers : [],
  }
}

export function enrichProducts(list) {
  return (list || []).map(enrichProduct)
}
