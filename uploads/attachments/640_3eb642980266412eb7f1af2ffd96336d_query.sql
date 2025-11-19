SELECT
  CONCAT_WS(';',  cabecera.NumAlbaran, cabecera.TimeStamp, cabecera.NombreCliente, cabecera.DireccionCliente, cabecera.DNICliente, cabecera.ImporteTotal, linea.Descripcion, linea.Peso, linea.Precio, linea.Importe) AS ConcatenatedFields
FROM sys_datos.dat_albaran_cabecera AS cabecera
JOIN sys_datos.dat_albaran_linea AS linea ON cabecera.IdAlbaran = linea.IdAlbaran
WHERE MONTH(cabecera.TimeStamp) = MONTH(NOW()) OR MONTH(cabecera.TimeStamp) = MONTH(NOW()) ;
