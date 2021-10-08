enum OdooType {
  STR = 1,
  INT,
  FLOAT,
  BOOL,
  LST_STR,
  LST_INT,
  LST_FLOAT,
  LAMBDA,
  ORM,
}

interface OdooObject {
  k?: string;
  otype: OdooType;
  v?: string;
  vInt?: number;
  vFloat?: number;
  vBool?: boolean;
  vListStr?: string[];
  vListInt?: number[];
  vListFloat?: number[];
}

interface OdooDomainItem {
  logical?: string;
  f: string;
  o: string;
  v: OdooObject;
}

type OdooContext = OdooObject[];
type OdooDomain = OdooDomainItem[];

export {
  OdooType,
  OdooObject,
  OdooDomainItem,
  OdooContext,
  OdooDomain,
}
