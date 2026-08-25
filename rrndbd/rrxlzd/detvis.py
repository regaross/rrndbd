"""Two-panel x–z outlines of XLZD cylinders, GPS source, and PW layers."""

from pathlib import Path
import json
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from ..base import TwoPanelBasePlot


_UNITS = {'m': 1.0, 'cm': 0.01, 'mm': 0.001, 'km': 1000.0}


def _strip_macro_line(raw):
    return raw.split('#', 1)[0].strip()


def _parse_macro(path):
    """Return {command: token list} from a Geant4 macro (last write wins)."""
    commands = {}
    for raw in Path(path).read_text().splitlines():
        line = _strip_macro_line(raw)
        if not line.startswith('/'):
            continue
        parts = line.split()
        commands[parts[0]] = parts[1:]
    return commands


def _to_metres(tokens):
    """Convert a GPS length token list (numbers + optional unit) to metres."""
    unit = 'm'
    values = []
    for token in tokens:
        key = token.lower()
        if key in _UNITS:
            unit = key
        else:
            values.append(float(token))
    scale = _UNITS[unit]
    return [v * scale for v in values]


def _resolve_geometry(geom_path, macro_path):
    """Return an existing JSON path, or None if nothing readable was found."""
    if not geom_path:
        return None
    path = Path(geom_path)
    if path.exists():
        return path
    name = path.name
    beside = Path(macro_path).parent / name
    if beside.exists():
        return beside
    parent = Path(macro_path).parent.parent / name
    if parent.exists():
        return parent
    return None


def _cylinder(ax, radius, height, z_center, **kwargs):
    ax.add_patch(
        Rectangle(
            (-radius, z_center - height / 2.0),
            2.0 * radius,
            height,
            fill=False,
            **kwargs,
        )
    )


def _draw_volume_cylinder(ax, x, radius, z_center, height, label='GPS volume'):
    ax.add_patch(
        Rectangle(
            (x - radius, z_center - height / 2.0),
            2.0 * radius,
            height,
            facecolor='crimson',
            edgecolor='crimson',
            lw=1.4,
            alpha=0.22,
            label=label,
            zorder=6,
        )
    )


def _draw_source(ax, x, z, radius, direction, arrow_length=0.35):
    colour = 'crimson'
    if radius is None or radius <= 0:
        ax.plot([x], [z], 'o', color=colour, ms=8, zorder=6, label='GPS source')
        xs = [x]
    else:
        ax.plot(
            [x - radius, x + radius],
            [z, z],
            color=colour,
            lw=3.0,
            zorder=6,
            label='GPS source',
        )
        pad = min(0.15, 0.2 * radius) if radius > 0.3 else 0.0
        xs = np.linspace(x - radius + pad, x + radius - pad, 7)

    if direction is None:
        return
    dx, _, dz = direction
    norm = np.hypot(dx, dz)
    if norm == 0:
        return
    ux, uz = dx / norm, dz / norm
    for xi in xs:
        ax.annotate(
            '',
            xy=(xi + ux * arrow_length, z + uz * arrow_length),
            xytext=(xi, z),
            arrowprops=dict(arrowstyle='-|>', color=colour, lw=1.4, mutation_scale=10),
            zorder=6,
        )


class DetectorOutline(TwoPanelBasePlot):
    """x–z slice of XLZD cylinders, GPS source, and nested PW layers.

    Driven by a Geant4 macro: ``/XLZD/setGeometry`` plus GPS position commands.
    ``geometry`` is an optional fallback JSON path used when the macro path
    is not readable. If neither exists, a warning is issued and only the
    GPS source is drawn.
    """

    def __init__(self, macro, geometry=None, figsize=(13.0, 7.2), title=None, **kwargs):
        super().__init__(figsize=figsize, **kwargs)

        self.macro = Path(macro)
        commands = _parse_macro(self.macro)
        self._load_geometry(commands, geometry)
        self._load_source(commands)
        self.draw()
        if title is not None:
            self.fig.suptitle(title, y=1.01)

    def _load_geometry(self, commands, geometry):
        self.has_detector = False
        self.geometry_path = None

        candidates = []
        geom_tokens = commands.get('/XLZD/setGeometry', [])
        if geom_tokens:
            candidates.append(geom_tokens[0])
        if geometry is not None:
            candidates.append(geometry)

        geom_path = None
        for candidate in candidates:
            resolved = _resolve_geometry(candidate, self.macro)
            if resolved is not None:
                geom_path = resolved
                break

        if geom_path is None:
            if geometry is None:
                detail = 'and no alternative was provided'
            else:
                detail = f'and the alternative {geometry!r} was not readable'
            warnings.warn(
                'No detector geometry found: the macro /XLZD/setGeometry path '
                f'is not accessible {detail}. Plotting source only.',
                UserWarning,
                stacklevel=3,
            )
            return

        geom = json.loads(Path(geom_path).read_text())
        self.geometry_path = Path(geom_path)
        self.has_detector = True

        od = geom['outerDetector']
        tpc = geom['TPC']
        pw = geom.get('ParallelWorlds', {})

        self.tpc_h = float(tpc['Height'])
        self.tpc_r = float(tpc['Diameter']) / 2.0
        self.od_h = float(od['Height'])
        self.od_r = float(od['Radius'])
        self.osv_h = float(od['OSV']['Height'])
        self.osv_r = float(od['OSV']['Radius'])
        self.balloon_h = float(od['Balloon']['Height'])
        self.balloon_r = float(od['Balloon']['Radius'])
        self.ocv_h = float(tpc['OCV']['FullHeight'])
        self.ocv_r = float(tpc['OCV']['Diameter']) / 2.0
        self.icv_h = float(tpc['ICV']['FullHeight'])
        self.icv_r = float(tpc['ICV']['Diameter']) / 2.0
        self.pw_r = np.asarray(pw.get('r', []), dtype=float)
        self.pw_hz = np.asarray(pw.get('z', []), dtype=float)
        self.pw_imp = np.asarray(pw.get('Importances', []), dtype=float)
        self.pw_center_z = self.tpc_h / 2.0

    def _load_source(self, commands):
        def first(key, default=None):
            tokens = commands.get(key, [])
            return tokens[0] if tokens else default

        centre = _to_metres(commands.get('/gps/pos/centre', ['0', '0', '0']))
        while len(centre) < 3:
            centre.append(0.0)
        self.source_x, self.source_y, self.source_z = centre[:3]

        radius_tokens = commands.get('/gps/pos/radius', [])
        self.source_r = _to_metres(radius_tokens)[0] if radius_tokens else 0.0
        halfz_tokens = commands.get('/gps/pos/halfz', [])
        self.source_hz = _to_metres(halfz_tokens)[0] if halfz_tokens else 0.0

        self.source_type = first('/gps/pos/type', 'Point')
        self.source_shape = first('/gps/pos/shape', '')
        self.source_confine = first('/gps/pos/confine')
        self.source_ang = first('/gps/ang/type')

        if '/gps/direction' in commands:
            direction = [float(t) for t in commands['/gps/direction']]
            while len(direction) < 3:
                direction.append(0.0)
            self.source_dir = tuple(direction[:3])
        else:
            self.source_dir = None

        particle = commands.get('/gps/particle', ['gamma'])
        self.particle = particle[0] if particle else 'gamma'
        energy = commands.get('/gps/ene/mono', [])
        self.energy = ' '.join(energy) if energy else ''

    def _is_volume_cylinder(self):
        if (self.source_type or '').lower() != 'volume':
            return False
        shape = (self.source_shape or '').lower()
        return shape == 'cylinder' or (not shape and self.source_hz > 0)

    def _confine_cylinder(self):
        if not self.source_confine or not self.has_detector:
            return None
        z0 = self.pw_center_z
        volumes = {
            'icv_proper': (0.0, self.icv_r, z0, self.icv_h),
            'ocv_proper': (0.0, self.ocv_r, z0, self.ocv_h),
            'tpc_proper': (0.0, self.tpc_r, z0, self.tpc_h),
        }
        return volumes.get(self.source_confine.lower())

    def _volume_cylinder(self):
        x, r, z = self.source_x, self.source_r, self.source_z
        h = 2.0 * self.source_hz
        confine = self._confine_cylinder()
        if confine is None:
            return x, r, z, h
        cx, cr, cz, ch = confine
        r_eff = min(r, cr)
        zmin = max(z - h / 2.0, cz - ch / 2.0)
        zmax = min(z + h / 2.0, cz + ch / 2.0)
        if zmax <= zmin:
            return x, r, z, h
        return cx, r_eff, 0.5 * (zmin + zmax), zmax - zmin

    def _place_source(self, ax, arrow_length=0.35):
        if self._is_volume_cylinder():
            x, r, z, h = self._volume_cylinder()
            if self.source_confine:
                label = f'GPS ({self.source_confine})'
            else:
                label = 'GPS volume'
            _draw_volume_cylinder(ax, x, r, z, h, label=label)
            return
        direction = self.source_dir
        if (self.source_ang or '').lower() == 'iso':
            direction = None
        _draw_source(
            ax,
            self.source_x,
            self.source_z,
            self.source_r,
            direction,
            arrow_length=arrow_length,
        )

    def _source_limits(self, pad):
        if self._is_volume_cylinder():
            x, r, z, h = self._volume_cylinder()
            x_span = max(r, 0.5) * 1.5 + pad
            return (x - x_span, x + x_span, z - h / 2.0 - pad, z + h / 2.0 + pad)
        span = max(self.source_r, 0.5) * 1.5 + pad
        return (
            self.source_x - span,
            self.source_x + span,
            self.source_z - span,
            self.source_z + span,
        )

    def draw(self):
        self._draw_overview(self.ax1)
        self._draw_zoom(self.ax2)

        particle = self.particle
        energy = self.energy or ''
        label = f'{energy} {particle}'.strip()
        if self._is_volume_cylinder():
            subtitle = r'$x$–$z$ slice of source volume'
        else:
            subtitle = r'$x$–$z$ slice of source plane'
        if self.has_detector:
            subtitle = subtitle + ' and importance layers'
        self.fig.suptitle(rf'{label}: {subtitle}', y=1.01)
        self.fig.tight_layout()

    def _draw_overview(self, ax):
        if self.has_detector:
            z0 = self.pw_center_z
            _cylinder(ax, self.od_r, self.od_h, z0, edgecolor='0.25', lw=1.4, label='OD')
            _cylinder(ax, self.osv_r, self.osv_h, z0, edgecolor='0.45', lw=1.1, ls='--', label='OSV')
            _cylinder(ax, self.balloon_r, self.balloon_h, z0, edgecolor='0.55', lw=1.0, ls=':', label='Balloon')
            _cylinder(ax, self.ocv_r, self.ocv_h, z0, edgecolor='steelblue', lw=1.1, label='OCV')
            _cylinder(ax, self.icv_r, self.icv_h, z0, edgecolor='royalblue', lw=1.1, label='ICV')
            _cylinder(ax, self.tpc_r, self.tpc_h, z0, edgecolor='black', lw=1.6, label='TPC')
            ax.set_xlim(-self.od_r * 1.05, self.od_r * 1.05)
            ax.set_ylim(z0 - self.od_h / 2 * 1.05, z0 + self.od_h / 2 * 1.05)
            ax.set_title('Overview (JSON geometry + GPS source)')
        else:
            xmin, xmax, zmin, zmax = self._source_limits(pad=0.55)
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(zmin, zmax)
            ax.set_title('Overview (GPS source)')

        self._place_source(ax, arrow_length=0.55)
        ax.set_aspect('equal')
        ax.set_xlabel(r'$x$ [m]')
        ax.set_ylabel(r'$z$ [m]')
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(loc='lower right', fontsize=8, frameon=True)

    def _draw_zoom(self, ax):
        if self.has_detector:
            z0 = self.pw_center_z
            _cylinder(ax, self.tpc_r, self.tpc_h, z0, edgecolor='black', lw=1.8, label='TPC')

            n_pw = len(self.pw_r)
            pw_cmap = plt.cm.Blues
            for i, (radius, half_z, importance) in enumerate(
                zip(self.pw_r, self.pw_hz, self.pw_imp)
            ):
                color = pw_cmap(0.30 + 0.70 * i / max(n_pw - 1, 1))
                ax.add_patch(
                    Rectangle(
                        (-radius, z0 - half_z),
                        2.0 * radius,
                        2.0 * half_z,
                        facecolor=color,
                        edgecolor='navy',
                        lw=0.9,
                        alpha=0.45,
                        label=fr'PW layer {i + 1} ($I={int(importance)}$)',
                        zorder=2 + i,
                    )
                )
            ax.axhline(z0, color='navy', ls=':', lw=0.8, alpha=0.6)
            zoom_x = max(self.tpc_r, abs(self.source_x) + self.source_r, 1.5) * 1.15
            ax.set_xlim(-zoom_x, zoom_x)
            zmin, zmax = -0.2, self.tpc_h + 0.2
            if self._is_volume_cylinder():
                _, _, vz, vh = self._volume_cylinder()
                zmin = min(zmin, vz - vh / 2.0) - 0.2
                zmax = max(zmax, vz + vh / 2.0) + 0.2
            ax.set_ylim(zmin, zmax)
            if self._is_volume_cylinder() and self.source_confine:
                source_note = f'source in {self.source_confine}'
            elif self._is_volume_cylinder():
                source_note = rf'source $z={self.source_z:g}\pm{self.source_hz:g}$ m'
            else:
                source_note = rf'source $z={self.source_z:g}$ m'
            ax.set_title(rf'TPC $z=0\to H$, PW centred at $z=H/2$, {source_note}')
        else:
            xmin, xmax, zmin, zmax = self._source_limits(pad=0.22)
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(zmin, zmax)
            ax.set_title(rf'Source $z={self.source_z:g}$ m')

        self._place_source(ax, arrow_length=0.22)
        ax.set_aspect('equal')
        ax.set_xlabel(r'$x$ [m]')
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            leg = ax.legend(
                loc='lower right',
                fontsize=8,
                frameon=True,
                facecolor='white',
                framealpha=1.0,
            )
            leg.set_zorder(20)
