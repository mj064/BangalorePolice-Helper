import pathlib
p = pathlib.Path('frontend/src/maps/HotspotMap.tsx')
t = p.read_text()
t = t.replace("  colorBy = 'pii',\n", "")
t = t.replace("  const colorByRef = useRef(colorBy);\n", "")
t = t.replace("  colorByRef.current = colorBy;\n", "")
t = t.replace("const colorField;\n    const colExpr = severityColor();\n", "const colExpr = severityColor('impact_score');\n")
p.write_text(t)
print('fixed')