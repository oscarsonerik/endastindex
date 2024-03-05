import pandas as pd
import matplotlib.pyplot as plt
from statistics import mean
print('')
""" Read CSV 
# Read the CSV file into a DataFrame - Se till så att det är rätt format. Kommatecken eller inte.
"""
def GetData(magazinsize, water_use, arean):
  df_365 = pd.read_csv('SMHI\SMHI_modified3.csv')
  df_med = pd.read_csv('SMHI\SMHI_modified_medel.csv')
  df_med_last_14 = pd.read_csv('SMHI\SMHI_2014_2020.csv',  delimiter=";", decimal=",")
  df_med_last_14.insert(0, 'ID', range(len(df_med_last_14)))
  """
  # Load data into variable
  """
  months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  # roofarea = 20                                   # m2
  # tanksize = 50                                    # m3 
  # wateruseday = 350 * 0.001                        # Gör om l/day tll m3/day. (l = dm3 --> 1m3 = 1000dm3)
  roofarea = arean                                   # m2
  tanksize = magazinsize                                    # m3 
  wateruseday = water_use * 0.001                        # Gör om l/day tll m3/day. (l = dm3 --> 1m3 = 1000dm3)

  ind = df_med_last_14["ID"]                       # Lägger till ID i första kolumnen
  day = df_med_last_14['Dag siffra']               # Dag
  month = df_med_last_14['Månad siffra']           # Månad
  year = df_med_last_14['År siffra']
  prec_mm = df_med_last_14['Nederbördsmängd']      # mm
  avrin_coef = 1          # !!! Kom ihåg att kolla upp avrin_coeff !!!
  prec_m = [i * avrin_coef * 0.001 for i in prec_mm]   # Gör om millimeter till meter
  prec_m3 = [i * roofarea for i in prec_m]             # Gör ny lista med area X nederbörd --> m3
  temp = df_med_last_14['Temperatur']                  # Celcius
  temp = [i for i in temp]
  vol_tank = 0
  tot_h2o_use = 0
  water_out = 0

  # Tester med variabler för robusethet och vid fel i koden
  # 1. Superstor tank --> Funkar
  # 2. Superliten tank --> Funkar
  # 3. Superhög användning per dag --> Funkar
  # 4. Superliten anvädning per dag --> Funkar
  # 5. Superlitet tak --> Funkar
  # 6. Superstort tak --> Funkar
  """
  Vattenbalansmodell
  """
  print("__Data mellan 2014-2022__")
  print(f'Vattenmängd som kommer in i systemet {round(sum(prec_m3),2)}')
  ret_svar = model_streamlit(ind, tanksize, vol_tank, tot_h2o_use, water_out, wateruseday, day, month, prec_m3, temp)
  print(f'Controll__prec_m3 sum: {round(sum(ret_svar[12]),2)}')
  return ret_svar

# plt.bar(ind,prec_m3)
# plt.show()
# plt.plot(ind,temp)
# plt.show()
# Modellen tar in data för år 2014-2022 och kör den för att sedan returnera hur/var vattnet befinner sig under de 9 åren.
# Modellen tar in regnvatten först i tanken (början av dagen), sedan tar den upp vatten till huset(slutet av dagen)

# Antaganden
# Antar att tanken inte fryser
# Antar att all snö på taket smälter på en dag vid plusgrader
def model_streamlit(ind, tanksize, vol_tank, tot_h2o_use, water_out, wateruseday, day, month, prec_m3, temp):
  # Create lists to hold datainfo
  monthly_collected_water = []
  monthly_lost_water = []
  cumulative_total = 0
  cum_water_use = []
  vattentanknivå = []
  drink_water_use = 0
  tak_lager  = previous_h2o = previous_water_out = counter = current_tot_h2o_use = current_water_out = 0
  total_water = 0
  current_month = 1
  water_out_temp = 0
  apnd_upptag = []
  apnd_water_tank = []
  apnd_water_out = []

  for i in ind:
    # Minusgrader
    if temp[i] < 0: # Kollar om det är snö eller regn
      # Påfyllnad
      tak_lager += prec_m3[i]      # Det är snö, bygger upp lager
      # Tömma tank
      if wateruseday < vol_tank:      # Ska ändå kunna ta från tanken vid slutet av dagen vid minusgrader
        vol_tank -= wateruseday       # Tar bort vatten från tanken
        tot_h2o_use += wateruseday   # Fyller på countern i total användning av regnvatten
        cumulative_total += wateruseday
        cum_water_use.append(cumulative_total)
        apnd_upptag.append(wateruseday)
      else:
        ##drink_water_use += vol_tank   # Mängd vatten som tas från kranvatten istället
        apnd_upptag.append(vol_tank)
        tot_h2o_use += vol_tank
        vol_tank -= vol_tank           # Tömmer tanken på det vatten som finns kvar i tanken
               # Fyller på countern i total anvädning av regnvatten (det som finns kvar i tanken)
        cumulative_total += wateruseday
        cum_water_use.append(cumulative_total)
    # Plusgrader
      apnd_water_out.append(0)
    else: 
      # # Påfyllnad
      # Tt = 0
      # melt_water = 2 * (temp[i]-Tt)
      # tak_lager -= melt_water
      if tanksize > vol_tank + prec_m3[i] + tak_lager:  # Checkar om tanken får plats med allt vatten 
        vol_tank += prec_m3[i] + tak_lager              # Beräknar vol_tankym, Antar att all snö smälter på en dag vid plusgrader
        tak_lager = 0                                    # Nollställer tak_lager
        apnd_water_out.append(0)
      else: # Om inte allt vatten får plats i tanken
        utrymme = tanksize - vol_tank
        water_out += prec_m3[i] + tak_lager - utrymme 
        water_out_temp += prec_m3[i] + tak_lager - utrymme
        apnd_water_out.append(water_out_temp)
        water_out_temp = 0
        vol_tank += utrymme                # Beräknar vol_tankym, # Antar att all snö på taket smälter på en dag vid plusgrader
        tak_lager = 0                     # Nollställer tak_lager
      # Tömma tank
      if wateruseday < vol_tank:           # Ta vatten från tanken vid slutet av dagen vid plusgrader
        apnd_upptag.append(wateruseday)
        vol_tank -= wateruseday            # Tar bort vatten från tanken
        tot_h2o_use += wateruseday        # Fyller på countern i total användning av regnvatten
        cumulative_total += wateruseday
        cum_water_use.append(cumulative_total)
      else:
        # Skulle nog kunna skriva de två kommande rader som: vol_tank -= vol_tank # tot_h2o_use += vol_tank
        apnd_upptag.append(vol_tank)
        tot_h2o_use += min(wateruseday, vol_tank)  # Fyller på countern i total anvädning av regnvatten (det som finns kvar i tanken)
        cumulative_total += wateruseday
        cum_water_use.append(cumulative_total)
        ##drink_water_use += vol_tank   # Mängd vatten som tas från kranvatten istället
        vol_tank -= min(wateruseday, vol_tank)      # Tömmer tanken på det vatten som finns kvar i tanken
    vattentanknivå.append(vol_tank)

    # # Kolla om det är ny månad för att lägga över månadsbesparning samt förlorad mängd
    # if month[i] == current_month:
    #   print(month[i])
    #   current_tot_h2o_use = tot_h2o_use - previous_h2o
    #   current_water_out = water_out - previous_water_out
    #   if day[i-1] == 365:
    #     monthly_collected_water.append(current_tot_h2o_use)
    #     monthly_lost_water.append(current_water_out)
    #   else:
    #     continue
    # else:
    #   monthly_collected_water.append(current_tot_h2o_use)
    #   monthly_lost_water.append(current_water_out)
    #   previous_h2o += current_tot_h2o_use
    #   previous_water_out += current_water_out 
    #   current_tot_h2o_use = current_water_out = 0
    #   current_month += 1 
    #   if current_month == 13:
    #     current_month == 1
    # counter += 1
  return (tot_h2o_use, water_out, vol_tank, tak_lager, counter, monthly_collected_water, monthly_lost_water, cum_water_use, vattentanknivå, drink_water_use, apnd_upptag, apnd_water_out, prec_m3)

def Make365(upptag, losten, prec_m3):
  yearss = 9  # Number of years
  values_per_year = 365
  avg_year_prec_m3 = []
  avg_year_upptag = []
  avg_year_lost = []
  for i in range(0,365):
      sum_prec_m3 = 0
      sum_upptag = 0
      sum_lost = 0
      for j in range(0,9):
          index = (j * values_per_year) + (i)
          sum_prec_m3 += prec_m3[index]
          sum_upptag += upptag[index]
          sum_lost += losten[index]

      average_prec_m3 = sum_prec_m3 / yearss
      average_upptag = sum_upptag / yearss
      average_lost = sum_lost / yearss
      avg_year_prec_m3.append(average_prec_m3)
      avg_year_upptag.append(average_upptag)
      avg_year_lost.append(average_lost)
  # Får fram average_year_upptag och average_year_vattenförlust
  return avg_year_upptag, avg_year_lost, avg_year_prec_m3

# # plt.plot(range(len(svar[7])), svar[7])
# # plt.xlabel('Dag på året')  # Label for x-axis
# # plt.ylabel('Cumulativt sparat dricksvatten')  # Label for y-axis
# # plt.title('Plot of svar[7]')  # Title of the plot
# #plt.show()
# #print(svar[8])
# plt.plot(range(len(svar[8])), svar[8])
# # plt.xlabel('Dag på året')  # Label for x-axis
# # plt.ylabel('Cumulativt sparat dricksvatten')  # Label for y-axis
# plt.title('Vattennivå i tank under året, börjar med 0')  # Title of the plot
# #plt.show()
# print(f'Vattenbehovet för ett år är {wateruseday*365} m3')
# print(f'Mängd dricksvatten som tvingas användas från kran {round(wateruseday*365 - svar[0], 3)} m3')
# print('(Drickvatten (kran) + upptaget regnvatten (tank) vara samma.)')

# plt.figure()
# # Plot månadsvis använt regnvatten i hus
# months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# plt.bar(months, svar[5], color='skyblue')
# plt.title('Använt regnvatten i byggnad m3')
# plt.xlabel('Month')
# plt.ylabel('m3')
# plt.xticks(rotation=45)
# #plt.show()

# # Plot månadsvis förlorat regnvatten ut
# plt.figure()
# plt.bar(months, svar[6], color='skyblue')
# plt.title('Regnvatten som går förlorat')
# plt.xlabel('Month')
# plt.ylabel('m3')
# plt.xticks(rotation=45)
# #plt.show()

# #def CallOnModel(tanksize, wateruseday, roof_area):
#   # Behöver lägg till ett steg där takarean omvandlas
# #  return model_streamlit(tanksize, vol_tank, tot_h2o_use, water_out, wateruseday, day, prec_m3, temp)
# '''
# '''
# '''
# Presentera nederbörd och temperatur för medelåret 2000-2022
# '''
# '''
# '''
# # Read the CSV file into a DataFrame - Se till så att det är rätt format. Kommatecken eller inte.
# df = pd.read_csv('SMHI_modified3.csv')
# df_med = pd.read_csv('SMHI_modified_medel.csv')

# prec_medel = df_med['Medel precip']
# temp_medel = df_med['Medel Temp']
# #print(prec_medel)
# #print(temp_medel)

# # Plot scatterplot för nederbörd av avg. månad
# plt.figure()
# plt.scatter(month, prec_m3, color='skyblue')
# plt.title('Mederlvärde nederbörd månad')
# plt.xlabel('Month')
# plt.ylabel('m3')
# plt.xticks(rotation=45)
# #plt.show()

# # Plot boxplot för nederbörd av avg. månad
# zippad = []
# # Iterate over both lists simultaneously
# for month, prec_m3 in zip(month, prec_m3):
#     # Create a tuple with values from both lists
#     pair = (month, prec_m3)
#     # Append the tuple to the result list
#     zippad.append(pair)
# # New list containing 12 sublists
# month_data = [[] for _ in range(12)]
# # Iterate over the original data and append values to corresponding sublists
# for item in zippad:
#     month1 = item[0]  # Extract the month value
#     month_data[month1 - 1].append(item[1])
# # Create a figure and axis object
# fig, ax = plt.subplots()
# # Create boxplots for each month
# ax.boxplot(month_data)
# ax.set_xticklabels(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
# ax.set_xlabel('Month')
# ax.set_ylabel('Data')
# plt.xticks(rotation=45)
# plt.title('Boxplot för varje månad av nederbördsdata')
# #plt.show()

# # SVÅRA Plot medelvärdet för nederbörden för varje månad
# avg_månad_med = []
# for i in month_data:
#     avg_månad_med.append(mean(i))
# #print(avg_månad_med)
# månad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
# plt.figure()
# plt.bar(månad, avg_månad_med, color='skyblue')
# plt.title('Mederlvärdeprec månad')
# plt.xlabel('Month')
# plt.ylabel('m3')
# plt.xticks(rotation=45)
# #plt.show()

# # LÄTTA Plot medelvärdet av nederbörden för varje månad
# prec_medel_m = [i * 0.001 for i in prec_medel]          # Gör om millimeter till meter
# prec_medel_m3 = [i * roofarea for i in prec_medel_m]    # Gör ny lista med area X nederbörd --> m3 
# månad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
# #plt.plot(month, temp, color='skyblue')
# plt.figure()
# plt.bar(månad, prec_medel_m3, color='skyblue')
# plt.title('Mederlvärdeprec månad')
# plt.xlabel('Month')
# plt.ylabel('m3')
# plt.xticks(rotation=45)
# #plt.show()
# # Stäng alla diagramfönster

# #plt.close('all')
# # Plot medelvärdet av temperaturen
# månad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
# #plt.plot(month, temp, color='skyblue')
# plt.figure()
# plt.bar(månad, temp_medel, color='skyblue')
# plt.title('Mederlvärde temp månad')
# plt.xlabel('Month')
# plt.ylabel('Celcius')
# plt.xticks(rotation=45)
# plt.show()

print('')