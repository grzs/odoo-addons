import { OdooType } from "./types";
import type {
  OdooObject,
  OdooDomainItem,
  OdooContext,
  OdooDomain,
} from "./types";

// type guard functions
function isOdooObject(obj: object): obj is OdooObject {
  return ((obj as OdooObject).otype !== undefined &&
          ((obj as OdooObject).v !== undefined ||
           (obj as OdooObject).vInt !== undefined ||
           (obj as OdooObject).vFloat !== undefined ||
           (obj as OdooObject).vBool !== undefined ||
           (obj as OdooObject).vListStr !== undefined ||
           (obj as OdooObject).vListInt !== undefined ||
           (obj as OdooObject).vListFloat !== undefined));
}

const createOdooObject = (obj, key=undefined) => {
  if (isOdooObject(obj)) { return obj; }

  switch (typeof obj) {
  case "string":
    return { otype: OdooType.STR, v: obj, k:key };
  case "number":
    if (String(obj).includes('.')) {
      return { otype: OdooType.FLOAT, v: String(obj), vFloat: obj, k:key };
    } else {
      return { otype: OdooType.INT, v: String(obj), vInt: obj, k:key };
    }
  case "boolean":
    return { otype: OdooType.BOOL, v: String(obj), vBool: obj, k:key };
  case "object":
    if (String(obj).includes(',')) {
      if (typeof obj[0] === "string") {
        const f = i => typeof i === "string";
        return { otype: OdooType.LST_STR, vListStr: obj.filter(f), k:key };
      }
      else if (typeof obj[0] === "number") {
        if (String(obj).includes('.')) {
          const f = i => typeof i === "number" && String(i).includes('.');
          return { otype: OdooType.LST_FLOAT, vListFloat: obj.filter(f), k:key };
        } else {
          const f = i => typeof i === "number" && i % 1 === 0;
          return { otype: OdooType.LST_INT, vListInt: obj.filter(f), k:key };
        }
      }
    }
  }
}

const createOdooContext = (context: object): OdooContext => {
  const oContext = [];
  for (const key in context) {
    const item = createOdooObject(context[key], key)
    item !== undefined && oContext.push(item);
  }
  return oContext;
}

const extractOdooContext = (oContext: OdooContext): object => {
  const context = {}
  for (const item of oContext) {
    if (typeof item.k !== "string") { continue }

    switch (item.otype) {
    case OdooType.STR:
      context[item.k] = item.v;
      continue;
    case OdooType.INT:
      context[item.k] = Number(item.v);
      continue;
    case OdooType.FLOAT:
      context[item.k] = Number(item.v);
      continue;
    case OdooType.BOOL:
      context[item.k] = Boolean(item.v);
      continue;
    case OdooType.LST_STR:
      context[item.k] = item.vListStr;
      continue;
    case OdooType.LST_INT:
      context[item.k] = item.vListInt;
      continue;
    case OdooType.LST_FLOAT:
      context[item.k] = item.vListFloat;
      continue;
    }
  }
  return context;
}

const createOdooDomain = (domain: Array<object>): OdooDomain => {
  function createDomainItem(item) {
    let logical = undefined; 
    if (item[0].length == 1 && "&|!".indexOf(item[0]) > -1) {
      logical = item.shift();
    }
    if (item.length == 3) {
      return {
        logical: logical,
        f: item[0],
        o: item[1],
        v: createOdooObject(item[2]),
      };
    }
  }

  const oDomain = []
  domain.forEach(item => {
    if (typeof item[0] !== "string") { return }
    oDomain.push(createDomainItem(item));
  });
  return oDomain;
}

export {
  isOdooObject,
  createOdooContext,
  extractOdooContext,
  createOdooDomain,
}
