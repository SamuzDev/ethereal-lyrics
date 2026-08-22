# Maintainer: samuz <samuz@archlinux.org>
pkgname=ethereal-lyrics
pkgver=0.1.0
pkgrel=1
pkgdesc="Display synced Spotify lyrics in your terminal with big block text"
arch=('any')
url="https://github.com/samuz/ethereal-lyrics"
license=('MIT')
depends=(
  'python'
  'python-rich'
  'python-spotipy'
  'python-httpx'
  'python-dotenv'
  'python-pydantic'
  'python-pydantic-settings'
  'python-dbus-python'
)
makedepends=(
  'python-build'
  'python-installer'
  'python-setuptools'
  'python-wheel'
)
source=("$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl
}
