// Only bundled illustrations may be used for the editor's local preview.
const assetUrls = new Map([
    ['automation', '/static/assets/automation.svg'],
    ['brand', '/static/assets/brand.svg'],
    ['landscape', '/static/assets/landscape.svg'],
    ['mesh', '/static/assets/mesh.svg'],
    ['motion', '/static/assets/motion.svg'],
    ['print', '/static/assets/print.svg'],
    ['rings', '/static/assets/rings.svg'],
    ['space', '/static/assets/space.svg'],
    ['spark', '/static/assets/spark.svg'],
    ['stack', '/static/assets/stack.svg'],
    ['visual', '/static/assets/visual.svg'],
    ['web', '/static/assets/web.svg'],
]);
export function assetUrl(id) {
    return assetUrls.get(id) ?? '/static/assets/web.svg';
}
