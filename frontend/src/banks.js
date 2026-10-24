// Fictional partner banks for the mock hand-off. Names, marks and copy are invented; only the
// general look (palette + layout conventions of large Indian retail banks) is echoed.
export const BANKS = {
  sentinel: { id: 'sentinel', name: 'Sentinel State Bank', tag: 'Banking for every citizen', cta: 'SUBMIT', nav: ['Personal', 'Cards', 'Loans', 'Deposits', 'Help'] },
  pinnacle: { id: 'pinnacle', name: 'Pinnacle Bank', tag: 'Banking, made simple', cta: 'Apply now', nav: ['Personal', 'Pay', 'Cards', 'Loans', 'Wealth'] },
  rosewood: { id: 'rosewood', name: 'Rosewood Bank', tag: 'Open to more', cta: 'Continue', nav: ['Accounts', 'Cards', 'Loans', 'Invest', 'Offers'] },
}

// Which partner serves which catalog product.
const PRODUCT_BANK = { P_01: 'pinnacle', P_02: 'sentinel', P_03: 'rosewood', P_04: 'pinnacle' }

export function bankFor(productId) {
  const ids = Object.keys(BANKS)
  const key = PRODUCT_BANK[productId] || ids[[...String(productId)].reduce((a, c) => a + c.charCodeAt(0), 0) % ids.length]
  return BANKS[key]
}
